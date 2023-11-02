import json
import random
import string

from channels.db import database_sync_to_async
from fcm_django.models import FCMDevice
import firebase_admin.messaging

from chat.models import Message
from chat.serializers.chat_serializer import ChatStateSerializer
from chat.serializers.message_serializer import MessageSerializer
from chat.utils.custom_json_encoder import CustomJSONEncoder
from events.models import Event
from users.models import User


# Create otp as a string
def create_otp():
    length = 6
    num = string.digits
    temp = random.sample(num, length)
    otp = "".join(temp)
    return otp


def duration_to_milliseconds(duration):
    seconds = duration * 60
    milliseconds = seconds * 1000

    return milliseconds


def send_notification(title, body, members, image, chat_id, chat_type):
    for member in members:
        device = FCMDevice.objects.get(registration_id=member)
        device.send_message(
            firebase_admin.messaging.Message(notification=firebase_admin.messaging.Notification(title=title, body=body, image=image),
                                             data={
                        'chat_id': f'{chat_id}',
                        'chat_type': f'{chat_type}'
                    })
        )
    return "sent"


def send_event_notification(event_type, title, body, image, event_id, user_id, members_ids):
    devices = FCMDevice.objects.filter(user_id__in=members_ids).exclude(user_id=user_id)
    event = Event.objects.filter(id=event_id).first()
    for device in devices:
        device = FCMDevice.objects.get(registration_id=f'{device.registration_id}')

        device.send_message(
            firebase_admin.messaging.Message(
                notification=firebase_admin.messaging.Notification(title=title, body=body, image=image),
                data={
                    'type': f'{event_type}',
                    'event_id': f'{event_id}',
                    'title': f'{event.title}',
                    'start_time': f'{event.start_date_time}',
                    'end_time': f'{event.end_date_time}',
                    'cover_image': f'{event.cover_image.url}' if event.cover_image else '',
                })
        )


def send_chat_notification(notification_type, title, body, chat_id, user_id, members_ids):
    print('send_chat_notification')
    devices = FCMDevice.objects.filter(user_id__in=members_ids).exclude(user_id=user_id)
    for device in devices:
        device = FCMDevice.objects.get(registration_id=f'{device.registration_id}')
        device.send_message(
            firebase_admin.messaging.Message(notification=firebase_admin.messaging.Notification(title=title, body=body),
                                             data={
                        'type': f'{notification_type}',
                        'chat_id': f'{chat_id}',
                        'title': f'{title}',
                        'text': f'{body}',
                    })
        )


def send_chat_message_notification(notification_type, message: Message, user_id, members_ids):
    sender_user = User.objects.filter(id=user_id).first()

    for members_id in members_ids:
        if members_id == user_id:
            continue

        contact_name = sender_user.phone
        # find contact name
        receiver_user = User.objects.filter(id=members_id).first()
        serialized_message = MessageSerializer(message, context={"user": receiver_user})
        serialized_message_data = serialized_message.data
        json_message = json.dumps(serialized_message_data, cls=CustomJSONEncoder)

        chat = message.chat

        chat_data = ChatStateSerializer(chat, context={"user": receiver_user}).data

        json_chat_data = None
        if chat_data:
            json_chat_data = json.dumps(chat_data, cls=CustomJSONEncoder)

        devices = FCMDevice.objects.filter(user_id=members_id)

        for device in devices:
            device = FCMDevice.objects.get(registration_id=f'{device.registration_id}')

            device.send_message(
                firebase_admin.messaging.Message(notification=firebase_admin.messaging.Notification(title=contact_name, body='New message'),
                                                 data={
                            'type': f'{notification_type}',
                            'chat_id': f'{message.chat_id}',
                            'chat_data': f'{json_chat_data}',
                            'message': f'{json_message}',
                        })
            )


@database_sync_to_async
def get_fcm_tokens(user_ids, exclude_user_id):
    return FCMDevice.objects.filter(user_id__in=user_ids).exclude(user_id=exclude_user_id)


@database_sync_to_async
def get_fcm_device(registration_id):
    return FCMDevice.objects.filter(registration_id=registration_id).first()


def send_any_notification(type, title, body, image, user_id, users_ids, data=None):
    data = data or {}
    data['type'] = f'{type}'
    devices = FCMDevice.objects.filter(user_id__in=users_ids).exclude(user_id=user_id)
    for device in devices:
        device = FCMDevice.objects.get(registration_id=f'{device.registration_id}')
        device.send_message(
            firebase_admin.messaging.Message(notification=firebase_admin.messaging.Notification(title=title, body=body, image=image), data=data)
        )
