from chat.models import Chat, Member, Message, SystemMessageAction
from chat.utils.ws_messaging import send_to_all_members_in_chat
from events.models import Event
from users.models import User
from datetime import datetime


def create_event_chat(event: Event, user: User):
    new_chat = Chat(chat_type=Chat.ChatTypes.EVENT, event=event)
    new_chat.save()

    event.chat_id = new_chat.id
    event.save()

    # add owner to chat
    new_member = Member(
        chat=new_chat,
        user=user,
        role=Member.Role.OWNER,
        status=Member.Status.ACTIVE,
        last_read_at=datetime.now(),
    )
    new_member.save()

    message = Message(
        type=Message.MessageTypes.SYSTEM,
        chat=new_chat,
        sender=new_member
    )
    message.save()
    system_message_action = SystemMessageAction(message=message)
    system_message_action.save()
    system_message_action.create_chat(new_chat)

    send_to_all_members_in_chat(
        message,
        False
    )

    return new_chat


def delete_event_chat(chat_id: int, user: User):
    chat = Chat.objects.get(id=chat_id)

    if chat is None:
        return

    member = Member.objects.filter(chat=chat, user=user).first()

    if member is None:
        return

    members = Member.objects.filter(chat=chat)
    chat.deleted_at = datetime.now()
    chat.save()

    for member in members:
        member.kicked_at = datetime.now()
        member.status = Member.Status.KICKED

        message = Message(
            type=Message.MessageTypes.SYSTEM,
            chat=chat,
            sender=member
        )
        message.save()
        system_message_action = SystemMessageAction(message=message)
        system_message_action.kick_member(member)

        send_to_all_members_in_chat(
            message,
            False
        )
