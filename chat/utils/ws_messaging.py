from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from chat.models import Message, Member, SystemMessageAction


def send_to_all_members_in_chat(message: Message, exclude_current_user=False, event: str = 'chat_message'):
    members = list(Member.objects.filter(chat=message.chat, status='Active'))

    message_action = SystemMessageAction.objects.filter(message=message).first()
    if message_action and message_action.target and message_action.target not in members:
        members.append(message_action.target)

    exclude_user_id = message.sender.user.id if exclude_current_user else None
    members_users_ids = [member.user_id for member in members if member.user_id != exclude_user_id]
    channel_layer = get_channel_layer()

    for member_user_id in members_users_ids:
        async_to_sync(channel_layer.group_send)(
            f'user_{member_user_id}', {
                'type': event,
                'message': message,
            }
        )


def send_to_members_in_chat(data: dict, members: list[Member], event: str = 'chat_message'):
    members_users_ids = [member.user_id for member in members]
    channel_layer = get_channel_layer()

    for member_user_id in members_users_ids:
        async_to_sync(channel_layer.group_send)(
            f'user_{member_user_id}', {
                'type': event,
                'data': data,
            }
        )
