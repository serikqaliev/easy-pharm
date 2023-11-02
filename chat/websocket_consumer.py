import json
from datetime import datetime, timezone

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from chat.models import Message, Member, Chat
from users.models import User
from utils.common import send_chat_message_notification
from .serializers.member_serializer import MemberSerializer
from .serializers.message_serializer import MessageSerializer
from .utils.custom_json_encoder import CustomJSONEncoder


class UserWebsocketConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.user = None
        self.room_group_name = None
        self.room_name = None

    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.get(id=user_id)

    async def connect(self):
        # user_id
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'user_{self.room_name}'
        self.user = await self.get_user(int(self.room_name))

        # set user online
        self.user.is_online = True
        sync_to_async(self.user.save)(update_fields=['is_online'])

        print('Connected:', self.room_group_name, self.room_name, self.channel_name)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, code):
        # set user offline
        self.user.is_online = False
        self.user.last_online = datetime.now(timezone.utc)
        sync_to_async(self.user.save)(update_fields=['is_online', 'last_online'])
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']

        print('text_data', text_data_json)

        if message_type == 'chat_message':
            data = text_data_json['data']

            await self.send_to_members_in_chat(
                data['chat_id'], {
                    'type': 'chat_message',
                    'message': data['message'],
                },
                {
                    'type': 'ChatNewMessage',
                    'message': data['message'],
                }
            )
        if message_type == 'message_deleted':
            data = text_data_json['data']

            await self.send_to_members_in_chat(
                data['chat_id'], {
                    'type': 'message_deleted',
                    'message': data['message'],
                },
                {
                    'type': 'ChatMessageDeleted',
                    'message': data['message'],
                }
            )
        if message_type == 'chat_deleted':
            data = text_data_json['data']

            await self.send_to_members_in_chat(
                data['chat_id'], {
                    'type': 'chat_deleted',
                    'chat_id': data['chat_id'],
                },
                {
                    'type': 'ChatDeleted',
                    'chat_id': data['chat_id'],
                }
            )
        elif message_type == 'start_typing':
            await self.send_to_members_in_chat(
                text_data_json['chat_id'], {
                    'type': 'start_typing',
                    'chat_id': text_data_json['chat_id'],
                    'user': self.user,
                },
            )
        elif message_type == 'stop_typing':
            await self.send_to_members_in_chat(
                text_data_json['chat_id'], {
                    'type': 'stop_typing',
                    'chat_id': text_data_json['chat_id'],
                    'user': self.user,
                },
            )
        elif message_type == 'message_read':
            await self.send_to_members_in_chat(
                text_data_json['chat_id'], {
                    'type': 'message_read',
                    'message_id': text_data_json['message_id'],
                },
            )
        elif message_type == 'chat_archived':
            await self.send_to_members_in_chat(
                text_data_json['chat_id'], {
                    'type': 'chat.archived',
                    'chat_id': text_data_json['chat_id'],
                    'archived': text_data_json['archived'],
                },
            )

    async def chat_deleted(self, event):
        await self.send(
            text_data=json.dumps({
                'type': 'chat_deleted',
                'chat_id': event['chat_id'],
                'created_at': datetime.now(timezone.utc).isoformat(),
            }, cls=CustomJSONEncoder)
        )

    async def message_deleted(self, event):
        message = event['message']
        await self.send(
            text_data=json.dumps({
                'type': 'message.deleted',
                'chat_id': message.chat.id,
                'message_id': message.id,
                'created_at': datetime.now(timezone.utc).isoformat(),
            }, cls=CustomJSONEncoder)
        )

    async def chat_archived(self, event):
        await self.send(
            text_data=json.dumps({
                'type': 'chat.archived',
                'chat_id': event['chat_id'],
                'archived': event['archived'],
                'created_at': datetime.now(timezone.utc).isoformat(),
            }, cls=CustomJSONEncoder)
        )

    async def chat_message(self, event):
        message = event['message']
        message_data = await MessageSerializer().async_serialization(
            event['message'],
            user=self.user
        )
        await self.send(
            text_data=json.dumps({
                'type': 'message.new',
                'chat_id': message.chat.id,
                'message': message_data,
                'created_at': datetime.now(timezone.utc).isoformat(),
            }, cls=CustomJSONEncoder)
        )

    async def send_to_members_in_chat(self, chat_id, data, notification=None):
        chat = await self.get_chat_from_db(chat_id)

        if chat:
            members = await self.get_chat_members(chat)
            members_user_ids = []

            for member in members:
                if member.participation_status == 'Active':
                    members_user_ids.append(member.user_id)
                    await self.channel_layer.group_send(
                        f'user_{member.user_id}',
                        data,
                    )

            if notification:
                await sync_to_async(send_chat_message_notification)(
                    notification_type=notification['type'],
                    message=data['message'],
                    user_id=self.user.id,
                    members_ids=members_user_ids,
                )

    async def message_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'MESSAGE_READ',
            'message_id': event['message_id'],
        }, cls=CustomJSONEncoder))

    async def start_typing(self, event):
        # get member of sender
        member = await self.get_chat_member(event['chat_id'], event['user'])
        member_data = await MemberSerializer().async_serialization(member, user=self.user)

        await self.send(text_data=json.dumps({
            'type': 'START_TYPING',
            'member': member_data,
            'chat_id': event['chat_id'],
        }))

    async def stop_typing(self, event):
        # get member of sender
        member = await self.get_chat_member(event['chat_id'], event['user'])
        member_data = await MemberSerializer().async_serialization(member, user=self.user)

        await self.send(text_data=json.dumps({
            'type': 'STOP_TYPING',
            'member': member_data,
            'chat_id': event['chat_id'],
        }))

    @database_sync_to_async
    def get_chat_from_db(self, room_name):
        return Chat.objects.filter(id=room_name).first()

    @database_sync_to_async
    def get_chat_message(self, message_id):
        return Message.objects.filter(id=message_id).first()

    @database_sync_to_async
    def get_chat_members(self, chat):
        return list(Member.objects.filter(chat=chat, participation_status='Active'))

    @database_sync_to_async
    def get_chat_member(self, chat_id, user):
        return Member.objects.filter(chat_id=chat_id, user=user).first()

