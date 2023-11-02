import json
from datetime import datetime, timedelta

import dateutil.parser
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from chat.models import Message, SystemMessageAction, Member, Chat
from chat.utils.ws_messaging import send_to_all_members_in_chat
from events.error_messages import ErrorMessages
from events.models import Event, Attachment, Invite, Location, Link
from events.serializers import GetInvitesSerializer, AttachmentSerializer, InviteSerializer, \
    ShortEventSerializer, EventProfileSerializer, LinkSerializer
from events.tasks import create_event_chat, delete_event_chat
from notifications.models import Notification
from notifications.serializers import ShortNotificationSerializer
from users.models import User
from utils.common import send_event_notification


def send_notifications_to_event_members(event_type, event, title, text, exclude_user_id, members_ids=None):
    print('send_notifications_to_event_members')
    if members_ids is None:
        members_ids = []
        members = Invite.objects.filter(event=event, status=Invite.Status.ACCEPTED).exclude(user_id=exclude_user_id)
        for member in members:
            members_ids.append(member.user.id)

    for member_id in members_ids:
        notification_history = Notification(
            notification_type='Event',
            event=event,
            user_id=member_id,
            notification_title=title,
            text=text,
        )
        notification_history.save()

    send_event_notification(
        event_type=event_type,
        title=title,
        body=text,
        image=f'https://backend.calendaria.kz/{event.cover_image.url}' if event.cover_image else None,
        event_id=int(event.id),
        user_id=exclude_user_id,
        members_ids=members_ids
    )


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def create_event(request):
    if request.method == 'POST':
        if not request.user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        title = request.data['title']
        all_day = request.data['all_day']

        start_date_time = dateutil.parser.isoparse(request.data['start_date_time'])
        end_date_time = dateutil.parser.isoparse(request.data['end_date_time'])

        # check if end_date is less than start_date
        if end_date_time < start_date_time:
            return Response({
                'message': ErrorMessages.START_DATE_MUST_BE_BEFORE_END_DATE
            }, status=status.HTTP_400_BAD_REQUEST)

        notice_before = request.data['notice_before']
        user_id = request.user.id
        event_type = request.data['event_type']
        location = request.data.get('location', None)
        description = request.data['description']
        cover_image = request.data.get('cover_image', None)

        recurrence_rule = request.data.get('recurrence_rule', None)
        user = User.objects.filter(id=user_id).first()
        event = Event(
            title=title,
            all_day=all_day,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
            notice_before=notice_before,
            author=user,
            type=event_type,
            description=description,
            cover_image=cover_image,
            recurrence_rule=recurrence_rule
        )
        event.save()

        if location:
            location = json.loads(location)
            print('location: ', location)
            print('address: ', location.get('address', None))

            new_location = Location(
                event=event,
                address=location.get('address', None),
                lng=location['lng'],
                lat=location['lat']
            )
            new_location.save()

            event.location = new_location
            event.save()

        # add owner to event
        new_invite = Invite(event=event, user=user, role='Owner', status='Accepted')
        new_invite.save()

        # if user want to create chat on event
        if request.data['create_chat']:
            create_event_chat(event, user)

        send_notifications_to_event_members(
            'EventCreated',
            event,
            f'New Event!',
            f'{user.username} created {event.title}',
            user.id,
            [user.id]
        )

        return Response({'event_id': event.id}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def create_chat_on_event(request, event_id):
    if request.user:
        event = Event.objects.filter(id=event_id).first()

        # check if event chat already exists
        if event.event_chat_id is not None:
            return Response({'message': 'chat already exists'}, status=status.HTTP_400_BAD_REQUEST)

        # check if user is owner of event
        if event.author != request.user:
            return Response({'message': 'you are not owner of event'}, status=status.HTTP_400_BAD_REQUEST)

        # create chat
        new_chat = Chat(chat_type="Event", event=event)
        new_chat.save()

        # add owner to chat
        new_member = Member(
            chat=new_chat,
            user=request.user,
            role="Owner"
        )
        new_member.save()

        # add all members to chat
        invites = Invite.objects.filter(event=event).exclude(user=request.user)
        for invite in invites:
            # check user permission
            user_permission = invite.user_permission

            new_member = Member(
                chat=new_chat,
                user=invite.user,
                role="Admin" if user_permission == 'Admin' else "User"
            )
            new_member.save()

        # add chat to event
        event.event_chat_id = new_chat.id
        event.save()

        # send notification to all members which are accepted invite
        members_ids = []
        for invite in invites:
            if invite.invite_status == 'Accepted':
                members_ids.append(invite.user.id)

        send_notifications_to_event_members(
            'EventChatCreated',
            event,
            f'New Chat!',
            f'{event.author.username} created chat for {event.title}',
            event.author.id,
            members_ids
        )

        # save notification history
        notification_history = Notification(
            notification_type='Event',
            event=event,
            user_id=event.author.id,
            notification_title=f'New Chat!',
            text=f'Chat for {event.title} created',
        )
        notification_history.save()

        return Response({"message": "chat created"}, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def delete_chat_on_event(request, event_id):
    if request.user:
        event = Event.objects.filter(id=event_id).first()
        chat = Chat.objects.filter(id=event.event_chat_id).first()
        if chat:
            event.event_chat_id = None
            event.save()
            chat.delete()

            send_notifications_to_event_members(
                'EventChatDeleted',
                event,
                f'Chat deleted',
                f'{request.user.username} deleted chat for {event.title}',
                request.user.id
            )
            return Response({"message": "chat deleted"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "chat not found"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def create_event_on_chat(request, chat_id):
    if request.method == 'POST':
        if request.user:
            title = request.data['title']
            all_day = request.data['all_day']
            start_date = datetime.strptime(str(request.data['start_date']), '%d-%m-%Y %H:%M:%S')
            end_date = datetime.strptime(str(request.data['end_date']), '%d-%m-%Y %H:%M:%S')
            notification_setting = request.data['notification_setting']
            repeat = request.data['repeat']
            user_id = request.user.id
            create_chat = request.data['create_chat']
            event_type = request.data['event_type']
            address = request.data['address']
            lng = request.data['lng']
            lat = request.data['lat']
            description = request.data['description']
            cover_image = request.data['cover_image']
            user = User.objects.filter(id=user_id).first()
            chat = Chat.objects.filter(id=chat_id).first()
            event = Event(
                title=title,
                all_day=all_day,
                start_date=start_date,
                end_date=end_date,
                notification_setting=notification_setting,
                repeat=repeat,
                author=user,
                create_chat=create_chat,
                event_type=event_type,
                description=description,
                cover_image=cover_image,
                event_chat_id=chat.id
            )
            event.save()
            chat.event = event
            chat.save()

            send_notifications_to_event_members(
                'ChatTransformedToEvent',
                event,
                f'Group chat transformed to event',
                f'{user.username} attached event {event.title} to the chat',
                user.id,
                [user.id]
            )

            return Response({'event_id': event.id}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def add_attachment(request):
    if request.method == 'POST':
        if request.user:
            event_id = request.data['event_id']
            attachment = request.data['attachment']
            attachment_type = request.data['attachment_type']
            user = request.user
            event = get_object_or_404(Event, id=event_id)

            created_attachment = Attachment.objects.create(
                attachment_type=attachment_type,
                event=event,
                author=user,
                attachment=attachment,
            )

            serializer = AttachmentSerializer(created_attachment, context={"user": request.user})

            send_notifications_to_event_members(
                'EventAttachmentsAdded',
                event,
                f'New attachment!',
                f'{user.username} added new attachment to {event.title}',
                user.id
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def delete_attachment(request):
    if not request.user:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    attachment_id = request.data['attachment_id']
    attachment = Attachment.objects.filter(id=attachment_id).first()

    # check if user is author or admin
    role = Invite.objects.filter(user=request.user, event=attachment.event).first().role

    is_admin_or_owner = role == 'Admin' or role == 'Owner'

    if attachment.author != request.user or not is_admin_or_owner:
        return Response({'message': 'you are not admin/owner or author'}, status=status.HTTP_400_BAD_REQUEST)

    Attachment.objects.filter(id=attachment_id).delete()

    send_notifications_to_event_members(
        'EventAttachmentsDeleted',
        attachment.event,
        f'Attachments deleted',
        f'{request.user.username} deleted attachments from {attachment.event.title}',
        request.user.id
    )
    return Response({'message': 'attachments are deleted'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def delete_attachments(request):
    if request.method == 'POST':
        if request.user:
            attachments = request.data['attachments']
            for attachment in attachments:
                Attachment.objects.filter(id=attachment).delete()

            send_notifications_to_event_members(
                'EventAttachmentsDeleted',
                attachment.event,
                f'Attachments deleted',
                f'{request.user.username} deleted attachments from {attachment.event.title}',
                request.user.id
            )
            return Response({'message': 'attachments are deleted'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def invite_users(request):
    if request.method == 'POST':
        if request.user:
            inviter = User.objects.filter(id=request.user.id).first()

            # get inviter name, username can be null or empty, so we check it
            if inviter.username:
                inviter_name = inviter.username
            else:
                inviter_name = inviter.phone

            participants = request.data['participants']
            # list of members to send notification
            participants_ids = []
            event_id = request.data['event_id']
            event = Event.objects.filter(id=event_id).first()

            for participant in participants:
                # check if user is already invited
                invite = Invite.objects.filter(user_id=participant['user_id'], event_id=event_id).first()
                if invite:
                    Response({'message': 'user invite already exists'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    participants_ids.append(participant['user_id'])

                    invitee = User.objects.filter(id=participant['user_id']).first()

                    new_invite = Invite(event=event, user=invitee, role=participant['user_permission'])
                    new_invite.save()

            # send_notifications_to_event_members(
            #     'EventRequest',
            #     event,
            #     f'New Event!',
            #     f'{inviter_name} invites you to {event.title}',
            #     request.user.id,
            #     participants_ids
            # )

            return Response({'message': 'users invited'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def invitation_respond(request, invite_id):
    if not request.user:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    invite_status = request.data['invite_status']

    invite = Invite.objects.filter(id=invite_id).first()
    invite.status = invite_status
    invite.save()

    # add user to chat if invite is accepted n chat exists
    if invite_status == Invite.Status.ACCEPTED and invite.event.chat_id is not None:
        chat = Chat.objects.filter(id=invite.event.chat_id).first()
        # find member in chat
        member = Member.objects.filter(chat=chat, user=request.user).first()
        if not member:
            Member.objects.create(
                chat=chat,
                user=request.user,
                role=invite.role
            )
        else:
            member.role = invite.role
            member.participation_status = 'Active'
            member.save()

    invitee_name = invite.user.username if invite.user.username else invite.user.phone

    if invite_status == Invite.Status.ACCEPTED:
        send_notifications_to_event_members(
            'EventAccepted',
            invite.event,
            f'Invitation accepted',
            f'{invitee_name} accepted invite to {invite.event.title}',
            invite.user.id)
    elif invite_status == Invite.Status.DECLINED:
        send_notifications_to_event_members(
            'EventDeclined',
            invite.event,
            f'Invitation declined',
            f'{invitee_name} declined invite to {invite.event.title}',
            invite.user.id)
    elif invite_status == Invite.Status.LEFT:
        send_notifications_to_event_members(
            'EventLeft',
            invite.event,
            f'Left the event',
            f'{invitee_name} left {invite.event.title}',
            invite.user.id)
    elif invite_status != Invite.Status.MAYBE:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response({'message': 'invite status changed'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def change_remind(request):
    if not request.user:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    remind = request.data['remind']
    invite_id = request.data['invite_id']

    invite = get_object_or_404(Invite, id=invite_id)

    if remind == Invite.Remind.ZERO:
        invite.remind_at = None
    else:
        invite.remind_at = datetime.now() + timedelta(minutes=int(remind))

    invite.remind = remind
    invite.save()

    invite_data = InviteSerializer(invite).data

    return Response(
        {
            'message': 'invite remind updated',
            'invite_data': invite_data
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_event_details(request, event_id):
    if not request.user:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    event = get_object_or_404(Event, id=event_id)
    data = EventProfileSerializer(event, context={"user": request.user}).data

    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_events(request):
    events = Event.objects.filter(
        invite__user_id=request.user.id
    ).exclude(
        invite__status__in=[
            Invite.Status.LEFT,
            Invite.Status.DECLINED
        ])

    serializer = ShortEventSerializer(events, many=True, context={"user": request.user})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_accepted_events(request):
    events = Event.objects.filter(invite__user_id=request.user.id, invite__status=Invite.Status.ACCEPTED)
    serializer = ShortEventSerializer(events, many=True, context={"user": request.user})

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_events_month(request, month, year):
    invites = Invite.objects.filter(user_id=request.user.id, event__start_date__year=str(year),
                                    event__start_date__month=str(month))
    serializer = GetInvitesSerializer(invites, many=True, context={"user": request.user})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_events_by_date(request, day, month, year):
    invites = Invite.objects.filter(user_id=request.user.id, event__start_date__year=str(year),
                                    event__start_date__month=str(month), event__start_date__day=str(day), )
    serializer = GetInvitesSerializer(invites, many=True, context={"user": request.user})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def delete_user(request):
    if request.method == 'POST':
        if request.user:
            invite_id = request.data['invite_id']
            invite = Invite.objects.filter(id=invite_id).first()
            notification_send = invite.status == Invite.Status.ACCEPTED
            invite.delete()

            if notification_send:
                send_notifications_to_event_members(
                    'EventMemberKicked',
                    invite.event,
                    f'Kicked from event',
                    f'You were removed from the event {invite.event.title}',
                    invite.user.id
                    [invite.user.id]
                )

            return Response({'message': 'invite deleted'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def change_permission(request):
    if request.method == 'POST':
        if request.user:
            invite_id = request.data['invite_id']
            permission = request.data['permission']
            invite = Invite.objects.filter(id=invite_id).first()
            invite.user_permission = permission
            invite.save()

            send_notifications_to_event_members(
                'EventRoleChanged',
                invite.event,
                f'Event role changed',
                f'Your role changed for the event {invite.event.title}',
                invite.user.id
                [invite.user.id]
            )

            return Response({'message': 'permission updated'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def delete_event(request):
    if request.method == 'POST':
        if request.user:
            event_id = request.data['event_id']
            event = Event.objects.filter(id=event_id).first()

            if event.chat_id is not None:
                chat = Chat.objects.filter(id=event.chat_id).first()
                chat.delete()

            send_notifications_to_event_members(
                'EventDeleted',
                event,
                f'Event deleted',
                f'{event.title} was deleted',
                event.author.id
            )
            event.delete()

            return Response({'message': 'event deleted'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def leave_event(request, event_id):
    if request.user:
        invite = get_object_or_404(Invite, event_id=event_id, user=request.user)

        if invite.role == Invite.Role.CREATOR:
            return Response(
                {'message': 'you can not leave event, because you are creator'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invite.status = Invite.Status.LEFT
        invite.save()

        return Response({'message': 'you leave event'}, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_event_history(request, event_id):
    notifications = Notification.objects.filter(event_id=event_id)
    serializer = ShortNotificationSerializer(notifications, many=True)
    return Response({'history': serializer.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def edit_event(request, event_id):
    if not request.user:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    event = get_object_or_404(Event, id=event_id)

    if event.author != request.user:
        return Response({'message': 'you are not author of event'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        title = request.data['title']
        all_day = request.data['all_day'] if 'true' in request.data['all_day'].lower() else False
        start_date = datetime.strptime(str(request.data['start_date_time']), '%d-%m-%Y %H:%M:%S')
        end_date = datetime.strptime(str(request.data['end_date_time']), '%d-%m-%Y %H:%M:%S')
        notification_setting = request.data['notice_before']
        print('notification_setting: ', notification_setting)
        recurrence_rule = request.data.get('recurrence_rule', None)
        event_type = request.data['event_type']
        description = request.data['description']
        create_chat = request.data['create_chat', None]

        # check if end_date is less than start_date
        if end_date < start_date:
            return Response({
                'message': ErrorMessages.START_DATE_MUST_BE_BEFORE_END_DATE
            }, status=status.HTTP_400_BAD_REQUEST)

        # check if event has cover_image
        # if event has cover, but request doesn't have cover, then delete cover
        # if event doesn't have cover, but request has cover, then add cover
        if event.cover_image and not request.data.get('cover_image', None):
            event.cover_image.delete()
        elif not event.cover_image and request.data.get('cover_image', None):
            event.cover_image = request.data.get('cover_image', None)

        # check if event has location
        # if event has location, but request doesn't have location, then delete location
        # if event doesn't have location, but request has location, then add location
        if event.location and not request.data.get('location', None):
            event.location = None
        elif not event.location and request.data.get('location', None):
            location = json.loads(request.data.get('location', None))
            new_location = Location(
                address=location.get('address', None),
                lng=location['lng'],
                lat=location['lat']
            )
            new_location.save()
            event.location = new_location

        event.title = title
        event.all_day = all_day
        event.start_date_time = start_date
        event.end_date_time = end_date
        event.notice_before = notification_setting
        event.recurrence_rule = recurrence_rule
        event.type = event_type
        event.description = description

        if create_chat is not None:
            if create_chat:
                if event.chat_id is None:
                    create_event_chat(event, request.user)
            else:
                if event.chat_id is not None:
                    delete_event_chat(event.chat_id, request.user)

        event.save()

        send_notifications_to_event_members(
            'EventUpdated',
            event,
            f'Event details updated',
            f'{event.title} was updated',
            event.author.id
        )

        return Response({'message': 'event updated'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_inbox(request):
    if request.method == 'GET':
        if request.user:
            invites = Invite.objects.filter(user=request.user)

            # get only waiting invites or remind_at is not null
            # the remind_at should be later than it is now.
            invites = invites.filter(
                status=Invite.Status.WAITING
            )

            events = []
            for invite in invites:
                events.append(invite.event)

            serializer = ShortEventSerializer(events, many=True, context={"user": request.user})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def add_links(request):
    if request.method == 'POST':
        if request.user:
            event_id = request.data['event_id']
            links = request.data['links']

            event = Event.objects.filter(id=event_id).first()

            # create link models for all links
            for link in links:
                new_link = Link(
                    author=request.user,
                    event=event,
                    url=link,
                )
                print(LinkSerializer(new_link, context={"user": request.user}).data)
                new_link.save()

            send_notifications_to_event_members(
                'EventLinksAdded',
                event,
                f'New links!',
                f'{request.user.username} added new links to {event.title}',
                request.user.id
            )

            return Response({'message': 'Links added'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_links(request, event_id):
    if request.method == 'GET':
        if request.user:
            event = Event.objects.filter(id=event_id).first()
            links = Link.objects.filter(event=event).distinct()

            serializer = LinkSerializer(links, many=True, context={"user": request.user})

            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def delete_link(request, link_id):
    if not request.user:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    link = Link.objects.filter(id=link_id).first()

    is_author = link.author == request.user

    if is_author:
        link.delete()
        return Response({'message': 'link deleted'}, status=status.HTTP_200_OK)

    current_user_role = Invite.objects.filter(user=request.user, event=link.event).first().role
    author_role = Invite.objects.filter(user=link.author, event=link.event).first().role
    can_delete = current_user_role == 'Admin' or current_user_role == 'Owner' or author_role == 'Admin' or author_role == 'Owner'

    if can_delete:
        link.delete()

        send_notifications_to_event_members(
            'EventLinksDeleted',
            link.event,
            f'Link deleted',
            f'{request.user.username} deleted link from {link.event.title}',
            request.user.id
        )
        return Response({'message': 'link deleted'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'you are not author or admin/owner'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_attachments(request, event_id):
    if not request.user:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    attachments = Attachment.objects.filter(event_id=event_id).order_by('-created_at')

    serializer = AttachmentSerializer(attachments, many=True, context={"user": request.user})

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def delete_all_events(request):
    if not request.user:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    Event.objects.filter(author=request.user).delete()
    return Response({'message': 'all events deleted'}, status=status.HTTP_200_OK)
