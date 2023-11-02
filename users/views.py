from datetime import datetime

import requests
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from fcm_django.models import FCMDevice
from rest_framework import status
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from chat.models import Chat, Member, Attachment
from chat.serializers.attachment_serializer import MediaAttachmentSerializer
from chat.serializers.chat_serializer import ChatStateSerializer
from events.models import Event, Invite
from events.serializers import ShortEventSerializer
from notifications.models import Notification
from users.models import User, Contact, Privacy, Settings, UserRelations
from users.serializers import UserSerializer, ContactSerializer, PrivacySerializer, SettingsSerializer, \
    ProfileUserSerializer
from users.utils.phone import get_e164_phone, format_phone_number
from utils.common import create_otp, send_any_notification


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def me_view(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
def create_user(request):
    if not request.method == 'POST':
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    phone = request.data['phone']
    device_token = request.data['device_token']
    otp = create_otp()

    user, created = User.objects.get_or_create(phone=phone)
    user.set_password(otp)
    user.save()

    send_message = requests.get(
        f'https://smsc.kz/sys/send.php?login=akzholqz&psw=01Cale02nda03ria&phones={phone}&mes=Код%20доступа%20Calendaria%20:%20{otp}'
    )

    if send_message.status_code == 200:
        device, created = FCMDevice.objects.get_or_create(registration_id=device_token)
        device.user = user
        device.save()
        user.save()
        return Response({'message': 'Success'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def change_avatar(request):
    if request.method == 'POST':
        if request.user:
            user = get_object_or_404(User, id=request.user.id)
            user.avatar = request.data.get('avatar', None)
            user.save()
            return Response({'message': 'avatar changed'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def activate_user(request):
    if request.method == 'POST':
        if request.user:
            username = request.data['username']
            time_zone = request.data['time_zone']

            user = get_object_or_404(User, id=request.user.id)
            user.username = username
            user.time_zone = time_zone
            user.in_calendaria = True

            privacy = Privacy(user=user)
            settings = Settings(user=user)

            privacy.save()
            settings.save()
            user.save()

            contacts = Contact.objects.filter(phone=user.phone)
            users_ids = [contact.user.id for contact in contacts]

            notification_title = f'{user.username} joined Calendaria'
            notification_text = f'Your contact is using Calendaria now'

            for contact in contacts:
                notification_history = Notification(
                    notification_type='Contact',
                    notification_contact=user,
                    user_id=contact.user.id,
                    notification_title=notification_title,
                    text=notification_text,
                )
                notification_history.save()

            send_any_notification(
                type='UserContactRegistered',
                title=notification_title,
                body=notification_text,
                image=user.avatar.url if user.avatar else None,
                user_id=user.id,
                users_ids=users_ids
            )

            return Response({'message': 'User activated'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def create_contact_list(request):
    if request.method == 'POST':
        current_user = User.objects.filter(id=request.user.id).first()
        received_contacts = request.data['contacts']
        for received_contact in received_contacts:
            label = received_contact.get('label', None)
            phone = received_contact['phone']
            contact_type = received_contact['type']

            try:
                phone = get_e164_phone(phone)
            except ValueError:
                phone = format_phone_number(phone)

            # check is me
            if phone == current_user.phone:
                continue

            # check contact is deleted
            deleted_contact = Contact.objects.filter(phone=phone, user=current_user).first()
            if deleted_contact:
                continue

            # check contact in calendaria
            in_calendaria = False
            user = User.objects.filter(phone=phone).first()
            if user:
                in_calendaria = True

                # create user relation if not exist
                UserRelations.objects.update_or_create(
                    user=current_user,
                    related_user=user
                )

            # get or create contact for comparing and updating
            contact, created = Contact.objects.get_or_create(
                label=label,
                type=contact_type,
                phone=phone,
                user=current_user,
                in_calendaria=in_calendaria
            )

            if contact:
                if label != contact.label:
                    contact.label = label
                if contact_type != contact.type:
                    contact.type = contact_type
                if phone != contact.phone:
                    contact.phone = phone
                if in_calendaria != contact.in_calendaria:
                    contact.in_calendaria = in_calendaria

        return Response({'message': 'user contacts updated'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def get_user_details(request, user_id):
    user = get_object_or_404(User, id=user_id)
    serializer = ProfileUserSerializer(user, context={"user": request.user})

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_contacts(request, page):
    if request.user:
        # get contacts order by label, in_calendaria
        registered = request.GET.get('registered', None)
        registered = {'true': True, 'false': False}.get(registered, None)

        if registered is not None:
            contacts = Contact.objects.filter(
                user=request.user,
                in_calendaria=registered,
                is_deleted=False
            ).order_by(
                '-in_calendaria',
                'label'
            )
        else:
            contacts = Contact.objects.filter(
                user=request.user,
                is_deleted=False
            ).order_by(
                '-in_calendaria',
                'label'
            )

        for contact in contacts:
            related_user = User.objects.filter(phone=contact.phone).first()

            if related_user:
                user_relations = UserRelations.objects.filter(user=request.user, related_user=related_user).first()

                if user_relations:
                    contact.in_calendaria = True
                    contact.save()
                    if user_relations.blocked:
                        contacts = contacts.exclude(id=contact.id)
                else:
                    contact.in_calendaria = True
                    contact.save()
                    UserRelations.objects.create(
                        user=request.user,
                        related_user=related_user,
                    )

        paginator = Paginator(contacts, 50)

        if page > paginator.num_pages:
            return Response(
                {
                    "message": "page does not exist"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        contacts = paginator.get_page(page)
        serializer = ContactSerializer(contacts, many=True)
        has_more = paginator.page(page).has_next()

        return Response({
            "contacts": serializer.data,
            "page": page,
            "pages": paginator.num_pages,
            "has_more": has_more
        }, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_blocked_contacts(request):
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    relations = UserRelations.objects.filter(user=request.user, blocked=True)

    contacts = Contact.objects.filter(user=request.user, phone__in=relations.values('related_user__phone'))

    serializer = ContactSerializer(contacts, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def add_new_contact(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        label = request.data.get('label')
        contact_type = request.data.get('type')
        phone = request.data.get('phone')

        try:
            phone = get_e164_phone(phone)
        except ValueError:
            phone = format_phone_number(phone)

        user = request.user

        if phone == user.phone:
            return Response({'message': 'You cannot add yourself'}, status=status.HTTP_400_BAD_REQUEST)

        in_calendaria = False
        existing_user = User.objects.filter(phone=phone).first()
        if existing_user:
            in_calendaria = True

            UserRelations.objects.update_or_create(
                user=request.user,
                related_user=existing_user
            )

        contact, created = Contact.objects.get_or_create(
            phone=phone,
            user=request.user
        )
        if not created:
            if contact.is_deleted:
                contact.is_deleted = False

            contact.label = label
            contact.type = contact_type
            contact.user = request.user
            contact.in_calendaria = in_calendaria
            contact.save()
            return Response(
                {
                    'message': 'Contact updated',
                    'updated': True
                }, status=status.HTTP_200_OK)
        else:
            contact.label = label
            contact.type = contact_type
            contact.in_calendaria = in_calendaria
            contact.save()

        return Response(
            {
                'message': 'Contact created',
                'updated': False
            }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def delete_contact(request, contact_id):
    contact = Contact.objects.filter(id=contact_id).first()
    if contact:
        contact.is_deleted = True
        contact.save()
        return Response({'message': 'Contact deleted'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Contact do not exist'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_privacy(request):
    if request.user:
        privacy = Privacy.objects.filter(user_id=request.user.id).first()
        serializer = PrivacySerializer(privacy)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_settings(request):
    if request.user:
        settings = Settings.objects.filter(user_id=request.user.id).first()
        serializer = SettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def update_settings(request):
    if request.method == 'POST':
        if request.user:
            theme = request.data['theme']
            settings = Settings.objects.filter(user_id=request.user.id).first()
            settings.theme = theme
            settings.save()
            return Response({'message': 'settings updated'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def update_privacy(request):
    if request.method == 'POST':
        if request.user:
            last_actions = request.data['last_actions']
            profile_image = request.data['profile_image']
            group_chat_invite = request.data['group_chat_invite']
            event_invite = request.data['event_invite']
            my_events = request.data['my_events_invite']
            privacy = Privacy.objects.filter(user_id=request.user.id).first()
            privacy.last_actions = last_actions
            privacy.profile_image = profile_image
            privacy.group_chat_invite = group_chat_invite
            privacy.event_invite = event_invite
            privacy.my_events = my_events
            privacy.save()
            return Response({'message': 'privacy updated'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def change_status(request):
    user = User.objects.filter(id=request.user.id).first()
    if user.is_online:
        user.is_online = False
        user.save()
        return Response({'message': 'User status offline'}, status=status.HTTP_200_OK)
    else:
        user.is_online = True
        user.save()
        return Response({'message': 'User status online'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def delete_user(request):
    User.objects.filter(id=request.user.id).delete()
    return Response({'message': 'user was deleted'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def change_shortdesc(request):
    shortdesc = request.data['status']
    user = request.user
    user.status = shortdesc
    user.status_change_at = datetime.utcnow()
    user.save()
    return Response({"message": "User status updated"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def mute_user(request, user_id):
    relation, created = UserRelations.objects.get_or_create(
        user=request.user,
        related_user_id=user_id
    )
    muted = relation.muted
    new_muted = not muted
    relation.muted = new_muted
    relation.save()

    # additionally mute chat if exist
    chat = Chat.objects.filter(
        chat_type='direct',
        member__user_id=request.user.id
    ).filter(
        member__user_id=user_id
    ).first()

    if chat:
        member = Member.objects.filter(
            chat=chat,
            user_id=request.user.id
        ).first()

        if new_muted:
            member.muted_at = datetime.now()
        else:
            member.muted_at = None

    return Response(
        {"muted": relation.muted},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def block_user(request, user_id):
    relation, created = UserRelations.objects.get_or_create(
        user=request.user,
        related_user_id=user_id
    )
    blocked = relation.blocked

    relation.blocked, message = not blocked, "User blocked" if not blocked else "User unblocked"
    relation.save()

    return Response({"message": message}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def update_contact(request):
    contact_id = request.data['contact_id']
    label = request.data['label']
    contact_type = request.data['type']
    phone = request.data['phone']

    phone = get_e164_phone(phone)

    contact = get_object_or_404(Contact, id=contact_id)
    contact.label, contact_type, phone = label, contact_type, phone
    contact.save()

    return Response({"message": "contact updated"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def update_user_autosave(request, user_id):
    relation, created = UserRelations.objects.get_or_create(
        user=request.user,
        related_user_id=user_id
    )
    autosave_media = relation.autosave_media
    relation.autosave_media = not autosave_media
    relation.save()

    return Response(
        {"message": "Autosave updated"},
        status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def logout(request):
    device_id = request.data['device_id']
    device = FCMDevice.objects.filter(registration_id=device_id).first()
    if device:
        device.delete()
    return Response({'message': 'User_logged out'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_common_groups(request, user_id):
    ids = [request.user.id, user_id]

    members = Member.objects.filter(
        user_id__in=ids,
        last_message__isnull=False
    ).order_by('-last_message__created_at').distinct()

    chats = Chat.objects.filter(member__in=members, chat_type='Group').distinct()

    if chats.count() == 0:
        return Response([], status=status.HTTP_200_OK)

    serializer = ChatStateSerializer(chats, many=True, context={"user": request.user})

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_common_events(request, user_id):
    events = Event.objects.filter(invite__user_id=request.user.id, invite__status=Invite.Status.ACCEPTED)\
        .filter(invite__user_id=user_id, invite__status=Invite.Status.ACCEPTED)
    serializer = ShortEventSerializer(events, many=True, context={"user": request.user})

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_common_media(request, user_id): # returns attachments with image, video types
    ids = [request.user.id, user_id]

    # find direct chat between two users
    chat = Chat.objects.filter(member__user_id__in=ids, chat_type='direct').first()

    if not chat:
        return Response([], status=status.HTTP_200_OK)

    # exclude File, Location, Contact, Event
    attachments = Attachment.objects.filter(chat=chat).exclude(
        attachment_type__in=['File', 'Location', 'Contact', 'Event']
    ).order_by("-created_at")

    if not attachments or len(attachments) == 0:
        return Response([], status=status.HTTP_200_OK)

    serializer = MediaAttachmentSerializer(attachments, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


