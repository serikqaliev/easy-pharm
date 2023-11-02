import json
import random
import string

from channels.db import database_sync_to_async
from fcm_django.models import FCMDevice
import firebase_admin.messaging


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
            firebase_admin.messaging.Message(
                notification=firebase_admin.messaging.Notification(title=title, body=body, image=image),
                data={
                    'chat_id': f'{chat_id}',
                    'chat_type': f'{chat_type}'
                })
        )
    return "sent"


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
            firebase_admin.messaging.Message(
                notification=firebase_admin.messaging.Notification(title=title, body=body, image=image), data=data)
        )
