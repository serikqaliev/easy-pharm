from datetime import datetime

from fcm_django.models import FCMDevice

from chat.models import Message, Chat, Member
from utils.common import send_notification


def save_chat_message(room_name, message_type, text, user_id):
    member = Member.objects.filter(user_id=user_id, chat_id=room_name).first()
    Chat.objects.filter(id=room_name).update(updated_at=datetime.now())
    if member.user.username:
        sender_data = member.user.username
    else:
        sender_data = member.user.phone
    message = Message(
        chat_id=room_name,
        member=member,
        text=text,
        message_type=message_type,
        sender=sender_data
    )
    message.save()

    chat = Chat.objects.filter(id=room_name).first()
    members = Member.objects.filter(chat_id=room_name).exclude(user_id=user_id)
    members_set = []
    for member_data in members:
        devices = FCMDevice.objects.filter(user=member_data.user)
        for device in devices:
            members_set.append(f'{device.registration_id}')

    if chat.chat_type == Chat.ChatTypes.DIRECT:
        if member.user.username:
            if member.user.avatar:
                send_notification(title=member.user.username, body=text, members=members_set,
                                  image=f'https://backend.calendaria.kz{member.user.avatar}',
                                  chat_id=chat.id, chat_type=chat.chat_type)
            else:
                send_notification(title=member.user.username, body=text, members=members_set,
                                  image=f'image url', chat_id=chat.id, chat_type=chat.chat_type)
        else:
            if member.user.avatar:
                send_notification(title=member.user.phone, body=text, members=members_set,
                                  image=f'https://backend.calendaria.kz{member.user.avatar}',
                                  chat_id=chat.id, chat_type=chat.chat_type)
            else:
                send_notification(title=member.user.phone, body=text, members=members_set,
                                  image=f'image url',chat_id=chat.id, chat_type=chat.chat_type)
    elif chat.chat_type == Chat.ChatTypes.GROUP:
        if chat.cover_image:
            send_notification(title=chat.title, body=text, members=members_set,
                              image=f'https://backend.calendaria.kz{chat.cover_image}',
                              chat_id=chat.id, chat_type=chat.chat_type)
        else:
            send_notification(title=chat.title, body=text, members=members_set,
                              image=f'image url', chat_id=chat.id, chat_type=chat.chat_type)
    elif chat.chat_type == Chat.ChatTypes.EVENT:
        event = chat.event
        if event.cover_image:
            send_notification(title=event.title, body=text, members=members_set,
                              image=f'https://backend.calendaria.kz{event.cover_image}',
                              chat_id=chat.id, chat_type=chat.chat_type)
        else:
            send_notification(title=event.title, body=text, members=members_set,
                              image=f'image url', chat_id=chat.id, chat_type=chat.chat_type)

    return message
