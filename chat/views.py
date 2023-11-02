import uuid
from datetime import datetime

from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from events.models import Event, Invite
from users.models import User, Contact, UserRelations
from chat.models import Message, SystemMessageAction, DeletedMessage, EventMessageAttachment, ContactMessageAttachment, \
    LocationMessageAttachment, Chat, Member, Attachment, Link
from .serializers.attachment_serializer import LinkSerializer, MediaAttachmentSerializer, \
    ContactAttachmentSerializer, LocationAttachmentSerializer, EventAttachmentSerializer
from .serializers.chat_serializer import ChatStateSerializer
from .serializers.member_serializer import MemberSerializer
from .serializers.message_serializer import MessageSerializer
from .utils.ws_messaging import send_to_all_members_in_chat, send_to_members_in_chat


def lobby(request, chat_id):
    return render(request, 'chat/lobby.html')


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_chats(request):
    if not request.user:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    user = request.user
    members = Member.objects.filter(
        user=user,
        last_message__isnull=False
    ).order_by('-last_message__created_at')

    chats = Chat.objects.filter(
        member__in=members,
        last_message__isnull=False,
        deleted_at__isnull=True
    ).order_by('-last_message__created_at')

    serialized = ChatStateSerializer(chats, many=True, context={"user": user})

    return Response({
        "chats": serialized.data,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def create_direct_chat(request):
    if not request.user:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    user_id = request.data.get('user_id', None)
    if request.user.id == user_id:
        return Response({"message": "You cannot create chat with yourself"}, status=status.HTTP_400_BAD_REQUEST)

    if not user_id:
        return Response({"message": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    second_user_id = user_id
    second_user = get_object_or_404(User, id=second_user_id)
    me = request.user

    old_chat = Chat.objects.filter(
        chat_type=Chat.ChatTypes.DIRECT,
        member__user=me
    ).filter(
        member__user=second_user
    ).first()

    if old_chat:
        member = Member.objects.filter(chat=old_chat, user=me).first()
        if not member:
            new_member = Member.objects.create(
                role='Participant',
                chat=old_chat,
                user=me,
                last_read_at=datetime.now(),
            )
            new_member.save()

        companion = Member.objects.filter(chat=old_chat, user=second_user).first()
        if not companion:
            new_member = Member.objects.create(
                role='Participant',
                chat=old_chat,
                user=second_user,
                last_read_at=datetime.now(),
            )
            new_member.save()

        return Response({"chat_id": old_chat.id}, status=status.HTTP_200_OK)

    chat = Chat.objects.create(
        chat_type=Chat.ChatTypes.DIRECT,
    )

    me_member = Member.objects.create(
        chat=chat,
        role='Participant',
        user=me,
        last_read_at=datetime.now(),
    )

    second_member = Member.objects.create(
        chat=chat,
        role='Participant',
        user=second_user,
        last_read_at=datetime.now(),
    )

    # get muted settings for second user if it exists in current user contacts
    # and mute chat if needed
    contact = Contact.objects.filter(phone=second_user.phone, user=me).first()
    if contact:
        relation_settings = UserRelations.objects.filter(
            user=me,
            related_user=second_user
        ).first()

        if relation_settings:
            if relation_settings.muted:
                second_member.muted_at = datetime.now()

    return Response({"chat_id": chat.id}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def create_group_chat(request):
    if request.method == 'POST':
        if request.user:
            user_ids = request.data['user_ids']
            title = request.data['title']
            cover_image = request.data.get('cover_image', None)
            description = request.data.get('description', None)

            chat = Chat(
                chat_type=Chat.ChatTypes.GROUP,
                title=title,
                description=description,
                cover_image=cover_image,
            )
            chat.save()

            me = Member(
                chat=chat,
                role=Member.Role.OWNER,
                user=request.user,
                last_read_at=datetime.now(),
            )
            me.save()

            for user_id in user_ids:
                user = User.objects.filter(id=user_id).first()
                member = Member(
                    chat=chat,
                    role=Member.Role.PARTICIPANT,
                    user=user,
                    last_read_at=datetime.now(),
                )
                member.save()

            message = Message(
                chat=chat,
                sender=me,
                type=Message.MessageTypes.SYSTEM
            )
            message.save()

            action = SystemMessageAction(message=message)
            action.create_chat(chat)

            chat.last_message = message
            chat.save()

            send_to_all_members_in_chat(
                message,
                False,
            )

            return Response({"chat_id": chat.id}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def create_event_chat(request):
    if not request.user:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    event_id = request.data.get('event_id', None)
    if not event_id:
        return Response({"message": "event_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    event = get_object_or_404(Event, id=event_id)
    if event.author != request.user:
        return Response({"message": "you are not owner of this event"}, status=status.HTTP_400_BAD_REQUEST)

    if event.chat_id:
        return Response({"chat_id": event.chat_id}, status=status.HTTP_200_OK)

    chat = Chat(
        chat_type='Event',
        event=event
    )
    chat.save()

    invites = Invite.objects.filter(event=event, invite_status='Accepted')

    for invite in invites:
        if invite.status == Invite.Status.ACCEPTED:
            member = Member(
                chat=chat,
                role=invite.user_permission,
                user=invite.user,
                last_read_at=datetime.now(),
            )
            member.save()

    me = Member.objects.filter(chat=chat, user=request.user).first()

    message = Message(
        chat=chat,
        member=me,
        type='System'
    )
    message.save()

    new_event_created_info_message = SystemMessageAction(
        action_type='EVENT_CHAT_CREATED',
        message=message,
        initiator=me,
    )
    new_event_created_info_message.save()

    chat.last_message = message
    chat.save()

    return Response({"chat_id": chat.id}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_chat(request, chat_id):
    user = request.user
    if not user:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    chat = Chat.objects.filter(id=chat_id).first()
    if not chat:
        return Response({"message": "chat not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = ChatStateSerializer(chat, context={"user": user})

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
def update_group_chat(request, chat_id):
    if not request.user:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    chat = get_object_or_404(Chat, id=chat_id)
    if chat.chat_type != Chat.ChatTypes.GROUP:
        return Response({"message": "chat is not group"}, status=status.HTTP_400_BAD_REQUEST)

    if chat.member_set.filter(user=request.user, role=Member.Role.OWNER).exists():
        title = request.data.get('title', None)
        description = request.data.get('description', None)
        cover_image = request.data.get('cover_image', None)

        if title:
            chat.title = title
        if description:
            chat.description = description
        if cover_image:
            chat.cover_image = cover_image

        chat.save()

        return Response({"message": "chat updated"}, status=status.HTTP_200_OK)
    else:
        return Response({"message": "you are not owner of this chat"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
def delete_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    member = get_object_or_404(Member, chat=chat, user=request.user)
    delete_for_all = request.data.get('delete_for_all', False)

    def truncate(truncate_for: Member):
        truncate_for.truncated_at = datetime.now()
        truncate_for.save()

    def leave():
        member.status = Member.Status.LEFT
        member.left_at = datetime.now()
        member.truncated_at = datetime.now()
        member.save()

        message = Message.objects.create(
            chat=chat,
            sender=member,
            type=Message.MessageTypes.SYSTEM
        )
        system_message = SystemMessageAction(message=message)
        system_message.left_member(member)

        send_to_all_members_in_chat(message, False)

    def delete():
        chat.deleted_at = datetime.now()
        chat.save()

    def delete_event_on_chat():
        event = chat.event
        event.chat = None
        event.save()

    def send_event(send_to_members: list[Member]):
        send_to_members_in_chat(data={
            "chat_id": chat.id,
        }, members=send_to_members, event='chat_deleted')

    if chat.chat_type == Chat.ChatTypes.DIRECT:
        if delete_for_all:
            members = Member.objects.filter(chat=chat)
            for it in members:
                truncate(it)

            send_event(members)
        else:
            truncate(member)
            send_event([member])
    elif chat.chat_type == Chat.ChatTypes.GROUP:
        if member.role == Member.Role.OWNER and delete_for_all:
            delete()
            members = Member.objects.filter(chat=chat)
            send_event(members)
        else:
            leave()
    elif chat.chat_type == Chat.ChatTypes.EVENT:
        if member.role == Member.Role.OWNER and delete_for_all:
            delete()
            delete_event_on_chat()
            members = Member.objects.filter(chat=chat)
            send_event(members)
        else:
            leave()

    return Response({"message": "chat deleted"}, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
def action_on_chat(request, chat_id, action):
    if action not in ['mute', 'unmute', 'archive', 'unarchive', 'pin', 'unpin']:
        return Response({"message": "action not found"}, status=status.HTTP_404_NOT_FOUND)

    chat = get_object_or_404(Chat, id=chat_id)
    member = get_object_or_404(Member, chat=chat, user=request.user)

    def notify_members(data: dict, members: list[Member], event: str):
        send_to_members_in_chat(data=data, members=members, event=event)

    if action == 'mute':
        member.muted_at = datetime.now()
        member.save()

        notify_members(data={
            'chat_id': chat.id,
            'muted': True,
        }, members=[member], event='chat_muted')
        return Response({"message": "chat muted"}, status=status.HTTP_200_OK)
    elif action == 'unmute':
        member.muted_at = None
        member.save()

        notify_members(data={
            'chat_id': chat.id,
            'muted': False,
        }, members=[member], event='chat_muted')
        return Response({"message": "chat unmuted"}, status=status.HTTP_200_OK)
    elif action == 'archive':
        member.archived_at = datetime.now()
        member.save()

        notify_members(data={
            'chat_id': chat.id,
            'archived': True,
        }, members=[member], event='chat_archived')
        return Response({"message": "chat archived"}, status=status.HTTP_200_OK)
    elif action == 'unarchive':
        member.archived_at = None
        member.save()

        notify_members(data={
            'chat_id': chat.id,
            'archived': False,
        }, members=[member], event='chat_archived')
        return Response({"message": "chat unarchived"}, status=status.HTTP_200_OK)
    elif action == 'pin':
        pinned_chats_count = Member.objects.filter(
            user=request.user,
            pinned_at__isnull=False
        ).count()
        if pinned_chats_count >= 3:
            return Response({"message": "you can pin only 3 chats"}, status=status.HTTP_400_BAD_REQUEST)
        member.pinned_at = datetime.now()
        member.save()

        notify_members(data={
            'chat_id': chat.id,
            'pinned': True,
        }, members=[member], event='chat_pinned')
        return Response({"message": "chat pinned"}, status=status.HTTP_200_OK)
    elif action == 'unpin':
        member.pinned_at = None
        member.save()

        notify_members(data={
            'chat_id': chat.id,
            'pinned': False,
        }, members=[member], event='chat_pinned')
        return Response({"message": "chat unpinned"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def join_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    member = get_object_or_404(Member, chat=chat, user=request.user)
    if member.status == Member.Status.KICKED:
        return Response({"message": "you are kicked from this chat"}, status=status.HTTP_400_BAD_REQUEST)

    member.status = Member.Status.ACTIVE
    member.left_at = None
    member.kicked_at = None
    member.save()

    message = Message.objects.create(
        chat=chat,
        sender=member,
        type=Message.MessageTypes.SYSTEM
    )
    system_message = SystemMessageAction(message=message)
    system_message.join_member(member)

    send_to_all_members_in_chat(message, system_message.action_type)

    return Response({"message": "you joined to chat"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def kick_member(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    member = get_object_or_404(Member, chat=chat, user=request.user)
    if member.role != Member.Role.OWNER and member.role != Member.Role.ADMIN:
        return Response({"message": "you can not kick member from this chat"}, status=status.HTTP_400_BAD_REQUEST)

    user_id = request.data.get('user_id', None)
    if not user_id:
        return Response({"message": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    if member.user_id == user_id:
        return Response({"message": "you can not kick yourself"}, status=status.HTTP_400_BAD_REQUEST)

    member_to_kick = get_object_or_404(Member, chat=chat, user_id=user_id)
    if member_to_kick.role == Member.Role.OWNER:
        return Response({"message": "you can not kick owner"}, status=status.HTTP_400_BAD_REQUEST)
    if member.role == Member.Role.ADMIN and member_to_kick.role == Member.Role.ADMIN:
        return Response({"message": "you can not kick admin"}, status=status.HTTP_400_BAD_REQUEST)

    member_to_kick.status = Member.Status.KICKED
    member_to_kick.kicked_at = datetime.now()
    member_to_kick.save()

    message = Message.objects.create(
        chat=chat,
        sender=member,
        type=Message.MessageTypes.SYSTEM
    )
    system_message = SystemMessageAction(message=message)
    system_message.kick_member(member_to_kick)

    send_to_all_members_in_chat(message, False)

    return Response({"message": "member kicked"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def leave_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    member = get_object_or_404(Member, chat=chat, user=request.user)

    member.status = Member.Status.LEFT
    member.left_at = datetime.now()
    member.save()

    message = Message.objects.create(
        chat=chat,
        sender=member,
        type=Message.MessageTypes.SYSTEM
    )
    system_message = SystemMessageAction(message=message)
    system_message.left_member(member)
    send_to_all_members_in_chat(message, system_message.action_type)

    return Response({"message": "you left chat"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def invite_members(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    member = get_object_or_404(Member, chat=chat, user=request.user)

    if member.role != Member.Role.OWNER and member.role != Member.Role.ADMIN:
        return Response({"message": "you can not invite members to this chat"}, status=status.HTTP_400_BAD_REQUEST)

    user_ids = request.data.get('user_ids', None)
    if not user_ids:
        return Response({"message": "user_ids is required"}, status=status.HTTP_400_BAD_REQUEST)

    members_to_create = []
    members_to_update = []

    for user_id in user_ids:
        user = User.objects.filter(id=user_id).first()
        if user:
            member = Member.objects.filter(chat=chat, user=user).first()
            if member:
                member.status = Member.Status.ACTIVE
                member.left_at = None
                member.kicked_at = None
                member.save()
                members_to_update.append(member)
            else:
                members_to_create.append(
                    Member(
                        chat=chat,
                        role=Member.Role.PARTICIPANT,
                        user=user,
                        last_read_at=datetime.now(),
                    )
                )

    Member.objects.bulk_create(members_to_create)

    added_members = members_to_create + members_to_update

    messages_to_send = []
    for added_member in added_members:
        message = Message.objects.create(
            chat=chat,
            sender=member,
            type=Message.MessageTypes.SYSTEM
        )
        system_message = SystemMessageAction(message=message)
        system_message.add_member(added_member)
        messages_to_send.append(message)

    for message in messages_to_send:
        send_to_all_members_in_chat(message, False)

    return Response({"message": "members invited"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def get_members(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    limit = request.data.get('limit', 30)
    from_member_id = request.data.get('from_member_id', None)
    if from_member_id:
        members = Member.objects.filter(
            chat=chat,
            id__lt=from_member_id
        ).order_by('-id')[:limit]
    else:
        members = Member.objects.filter(chat=chat).order_by('-id')[:limit]

    serializer = MemberSerializer(members, many=True)

    return Response(
        {
            "members": serializer.data,
            "next_id": members.last().id if members.last() else None
        },
        status=status.HTTP_200_OK
    )


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
def change_member_role(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    member = get_object_or_404(Member, chat=chat, user=request.user)

    if member.role != Member.Role.OWNER and member.role != Member.Role.ADMIN:
        return Response({"message": "you can not change member role in this chat"}, status=status.HTTP_403_FORBIDDEN)

    user_id = request.data.get('user_id', None)
    if not user_id:
        return Response({"message": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    role = request.data.get('role', None)
    if not role:
        return Response({"message": "role is required"}, status=status.HTTP_400_BAD_REQUEST)

    role = role.capitalize()
    if role not in [Member.Role.ADMIN, Member.Role.PARTICIPANT]:
        return Response({"message": "role is invalid"}, status=status.HTTP_400_BAD_REQUEST)

    member_to_change = get_object_or_404(Member, chat=chat, user_id=user_id)
    if member_to_change.role == Member.Role.OWNER:
        return Response({"message": "you can not change owner role"}, status=status.HTTP_403_FORBIDDEN)
    if member.role == Member.Role.ADMIN and member_to_change.role == Member.Role.ADMIN:
        return Response({"message": "you can not change admin role"}, status=status.HTTP_403_FORBIDDEN)

    member_to_change.role = role
    member_to_change.save()

    message = Message.objects.create(
        chat=chat,
        sender=member,
        type=Message.MessageTypes.SYSTEM,
    )
    system_message = SystemMessageAction(message=message)
    system_message.change_member_role(member_to_change, role)

    send_to_all_members_in_chat(message, False)

    return Response({"message": "member role changed"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def send_message(request, chat_id):
    cuuid = request.data.get('uuid')
    text = request.data.get('text', None)
    attachments = request.data.get('attachments', None)  # []
    attached_event = request.data.get('event', None)
    contact = request.data.get('contact', None)
    location = request.data.get('location', None)
    if not text:
        if not attachments and not attached_event and not contact and not location:
            return Response(
                {"message": "text, attachments, event_id, contact or location is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
    replayed_message_id = request.data.get('replayed_message_id', None)

    member = get_object_or_404(Member, chat_id=chat_id, user=request.user)
    message = Message.objects.create(
        uuid=cuuid,
        text=text,
        chat_id=chat_id,
        sender_id=member.id,
        type=Message.MessageTypes.DEFAULT,
        replay_to_id=replayed_message_id
    )

    event_attachment = None
    contact_attachment = None
    if attached_event:
        event = attached_event.get('event_data', None)
        if not event:
            return Response({"message": "event_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        event_id = event.get('id', None)
        if not event_id:
            return Response({"message": "event_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        event = get_object_or_404(Event, id=event_id)
        event_attachment = EventMessageAttachment.objects.create(
            event=event
        )
    if contact:
        user_data = contact.get('user_data', None)
        contact_data = contact.get('contact_data', None)
        contact_attachment = ContactMessageAttachment.objects.create(
            user_id=user_data.get('id', None) if user_data else None,
            contact_id=contact_data.get('id')
        )
    if location:
        LocationMessageAttachment.objects.create(
            latitude=location.get('latitude', None),
            longitude=location.get('longitude', None),
        )

    message.event = event_attachment
    message.contact = contact_attachment
    message.save()

    send_to_all_members_in_chat(
        message,
        False
    )

    serialized = MessageSerializer(message, context={"user": request.user})

    return Response({"message": serialized.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def get_messages(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    member = get_object_or_404(Member, chat=chat, user=request.user)

    pinned_only = request.data.get('pinned_only', False)
    limit = request.data.get('limit', 30)
    from_message_id = request.data.get('from_message_id', None)
    to_message_id = request.data.get('to_message_id', None)

    truncated_at = member.truncated_at
    left_at = member.left_at
    kicked_at = member.kicked_at

    dates = [date for date in [truncated_at, left_at, kicked_at] if date is not None]

    greatest_date = max(dates) if dates else None

    if from_message_id is not None and to_message_id is not None:
        if greatest_date:
            combined_filter = (
                    Q(chat=chat, id__gt=from_message_id, id__lt=to_message_id, created_at__gt=greatest_date)
                    |
                    Q(sender=member, message__chat=chat, message__id__lt=from_message_id,
                      message__created_at__gt=greatest_date)
            )
        else:
            combined_filter = (
                    Q(chat=chat, id__gt=from_message_id, id__lt=to_message_id)
                    |
                    Q(sender=member, message__chat=chat, message__id__lt=from_message_id)
            )
    elif from_message_id is not None and to_message_id is None:
        if greatest_date:
            combined_filter = (
                    Q(chat=chat, id__gt=from_message_id, created_at__gt=greatest_date)
                    |
                    Q(sender=member, message__chat=chat, message__id__lt=from_message_id,
                      message__created_at__gt=greatest_date)
            )
        else:
            combined_filter = (
                    Q(chat=chat, id__gt=from_message_id)
                    |
                    Q(sender=member, message__chat=chat, message__id__lt=from_message_id)
            )
    elif from_message_id is None and to_message_id is not None:
        if greatest_date:
            combined_filter = (
                    Q(chat=chat, id__lt=to_message_id, created_at__gt=greatest_date)
                    |
                    Q(sender=member, message__chat=chat, message__created_at__gt=greatest_date)
            )
        else:
            combined_filter = (
                    Q(chat=chat, id__lt=to_message_id)
                    |
                    Q(sender=member, message__chat=chat)
            )
    else:
        if greatest_date:
            combined_filter = (
                    Q(chat=chat, created_at__gt=greatest_date)
                    |
                    Q(sender=member, message__chat=chat, message__created_at__gt=greatest_date)
            )
        else:
            combined_filter = (
                    Q(chat=chat)
                    |
                    Q(sender=member, message__chat=chat)
            )

    combined_messages = Message.objects.filter(combined_filter).order_by('-created_at')

    deleted_message_ids = DeletedMessage.objects.filter(
        member=member,
        message__in=combined_messages
    ).values_list(
        'message_id', flat=True
    )

    messages = list(combined_messages.exclude(id__in=deleted_message_ids)[:limit])

    serialized = MessageSerializer(messages, many=True, context={"user": request.user})

    response_data = {
        "messages": serialized.data,
        "next_to_id": messages[-1].id if messages else None,
        "next_from_id": messages[0].id if messages else None,
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
def pin_unpin_message(request, chat_id: int, message_id: int):
    pin = request.data.get('pin', False)
    message = get_object_or_404(Message, id=message_id)
    member = get_object_or_404(Member, chat=message.chat, user=request.user)

    if pin:
        pinned_msgs_count = Message.objects.filter(
            chat=message.chat,
            pinned_at__isnull=False
        ).count()
        if pinned_msgs_count >= 3:
            return Response({"message": "you can pin only 3 messages"}, status=status.HTTP_400_BAD_REQUEST)

        if message.pinned_at is not None:
            return Response({"message": "message already pinned"}, status=status.HTTP_400_BAD_REQUEST)

        message.pinned_at = datetime.now()
        message.pinned_by = member
        message.save()

    else:
        if message.pinned_at is None:
            return Response({"message": "message already unpinned"}, status=status.HTTP_400_BAD_REQUEST)

        message.pinned_at = None
        message.pinned_by = None
        message.save()

    new_pinned = message.pinned_at is not None
    new_message = Message.objects.create(
        chat=message.chat,
        sender=member,
        type=Message.MessageTypes.SYSTEM
    )
    system_message = SystemMessageAction(message=new_message)
    if new_pinned:
        system_message.pin_message(message)
    else:
        system_message.unpin_message(message)

    send_to_all_members_in_chat(new_message, False)

    serialized = MessageSerializer(message, context={"user": request.user})
    return Response({"message": serialized.data}, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
def mark_read(request, chat_id, message_id):
    member = get_object_or_404(Member, chat_id=chat_id, user=request.user)

    def make_member_read(dt: datetime):
        member.last_read_at = dt
        member.save()

    if not message_id or message_id == 0:
        make_member_read(datetime.now())
    else:
        message = Message.objects.filter(id=message_id).first()
        make_member_read(message.created_at)

    return Response({"message": "message marked as read"}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
def delete_message(request, chat_id, message_id):
    get_object_or_404(Member, chat_id=chat_id, user=request.user)

    message = Message.objects.filter(id=message_id).first()
    for_all = request.data.get('for_all', False)

    if not message:
        return Response({"message": "message not found"}, status=status.HTTP_404_NOT_FOUND)

    if for_all:
        message.deleted_at = datetime.now()
        message.save()

    DeletedMessage.objects.create(
        member_id=request.user.id,
        message_id=message_id,
    )

    send_to_all_members_in_chat(
        message,
        False,
    )

    message = Message.objects.filter(id=message_id).first()
    serializer = MessageSerializer(message, context={"user": request.user})

    return Response({"message": serializer.data}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
def truncate_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    member = get_object_or_404(Member, chat=chat, user=request.user)

    member.truncated_at = datetime.now()
    member.save()

    return Response({"message": "chat truncated"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def get_chat_attached_media(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    limit = request.data.get('limit', 30)
    from_attachment_id = request.data.get('from_attachment_id', None)
    to_attachment_id = request.data.get('to_attachment_id', None)
    attachment_type = request.data.get('attachment_type', None)

    if attachment_type not in [Attachment.AttachmentType.IMAGE, Attachment.AttachmentType.VIDEO,
                               Attachment.AttachmentType.FILE]:
        return Response({"message": "attachment_type is invalid"}, status=status.HTTP_400_BAD_REQUEST)

    image_attachments = Attachment.objects.filter(
        message__chat=chat,
        type=attachment_type,
        id__gt=from_attachment_id,
        id__lt=to_attachment_id,
    ).order_by('-id')[:limit]

    serialized = MediaAttachmentSerializer(image_attachments, many=True)
    return Response({
        "attachments": serialized.data,
        "next_to_id": image_attachments.last().id if image_attachments.last() else None,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def get_chat_attached_contacts(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    limit = request.data.get('limit', 30)
    from_contact_id = request.data.get('from_contact_id', None)
    to_contact_id = request.data.get('to_contact_id', None)

    contacts = ContactMessageAttachment.objects.filter(
        message__chat=chat,
        id__gt=from_contact_id,
        id__lt=to_contact_id,
    ).order_by('-id')[:limit]

    serialized = ContactAttachmentSerializer(contacts, many=True)

    return Response({
        "contacts": serialized.data,
        "next_to_id": contacts.last().id if contacts.last() else None,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def get_chat_attached_locations(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    from_location_id = request.data.get('from_location_id', None)
    to_location_id = request.data.get('to_location_id', None)

    locations = LocationMessageAttachment.objects.filter(
        message__chat=chat,
        id__gt=from_location_id,
        id__lt=to_location_id,
    )

    serialized = LocationAttachmentSerializer(locations, many=True)

    return Response({
        "locations": serialized.data,
        "next_to_id": locations.last().id if locations.last() else None,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def get_chat_attached_events(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    from_event_id = request.data.get('from_event_id', None)
    to_event_id = request.data.get('to_event_id', None)

    events = EventMessageAttachment.objects.filter(
        message__chat=chat,
        id__gt=from_event_id,
        id__lt=to_event_id,
    ).order_by('-id')

    serialized = EventAttachmentSerializer(events, many=True)

    return Response({
        "events": serialized.data,
        "next_to_id": events.last().id if events.last() else None,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def get_chat_attached_links(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    from_link_id = request.data.get('from_link_id', None)
    to_link_id = request.data.get('to_link_id', None)

    links = Link.objects.filter(
        message__chat=chat,
        id__gt=from_link_id,
        id__lt=to_link_id,
    ).order_by('-id')

    serialized = LinkSerializer(links, many=True)

    return Response({
        "links": serialized.data,
        "next_to_id": links.last().id if links.last() else None,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def upload_attachment(request, chat_id):
    attachment_type = request.data.get('type', None)
    if not attachment_type or attachment_type not in [Attachment.AttachmentType.IMAGE, Attachment.AttachmentType.VIDEO,
                                                      Attachment.AttachmentType.FILE]:
        return Response({"message": "type is required and must be image/video/file"},
                        status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES.get('file', None)
    if not file:
        return Response({"message": "file is required"}, status=status.HTTP_400_BAD_REQUEST)

    chat = get_object_or_404(Chat, id=chat_id)
    member = get_object_or_404(Member, chat=chat, user=request.user)

    if member.status != member.Status.ACTIVE:
        return Response({"message": "you are not active in this chat"}, status=status.HTTP_400_BAD_REQUEST)

    attachment = Attachment.objects.create(
        message__chat=chat,
        message__sender=member,
        type=attachment_type,
        file=file
    )

    serialized = MediaAttachmentSerializer(attachment)

    return Response({"attachment": serialized.data}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
def delete_attachment(request, attachment_id):
    attachment = get_object_or_404(Attachment, id=attachment_id)

    attachment.is_deleted = True
    attachment.save()

    return Response({"message": "attachment deleted"}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
def delete_contact(request, contact_id):
    contact = get_object_or_404(ContactMessageAttachment, id=contact_id)

    contact.deleted_at = datetime.now()
    contact.save()

    return Response({"message": "contact deleted"}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
def delete_location(request, location_id):
    location = get_object_or_404(LocationMessageAttachment, id=location_id)

    location.deleted_at = datetime.now()
    location.save()

    return Response({"message": "location deleted"}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
def delete_event(request, event_id):
    event = get_object_or_404(EventMessageAttachment, id=event_id)

    event.deleted_at = datetime.now()
    event.save()

    return Response({"message": "event deleted"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def delete_all_attachments(request, chat_id):
    attachments = Attachment.objects.filter(chat_id=chat_id)
    for attachment in attachments:
        attachment.is_deleted = True
        attachment.save()
    return Response({"message": "all attachments deleted"}, status=status.HTTP_200_OK)
