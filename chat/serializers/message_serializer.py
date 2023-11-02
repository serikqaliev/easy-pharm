from asgiref.sync import sync_to_async
from rest_framework import serializers

from chat.models import Message, SystemMessageAction, ContactMessageAttachment
from events.serializers import ShortEventSerializer
from users.serializers import ContactSerializer
from .member_serializer import MemberSerializer
from .system_message_serializer import SystemMessageActionSerializer


class MessageSerializer(serializers.ModelSerializer):
    replayed_message = serializers.SerializerMethodField('replayed_message_set', read_only=True)
    sender = serializers.SerializerMethodField('sender_data_set', read_only=True)
    is_pinned = serializers.SerializerMethodField('is_pinned_set', read_only=True)
    pinned_by = serializers.SerializerMethodField('pinned_by_set', read_only=True)
    action = serializers.SerializerMethodField('action_set', read_only=True)
    contact = serializers.SerializerMethodField('contact_set', read_only=True)
    event = serializers.SerializerMethodField('event_set', read_only=True)

    def event_set(self, instance):
        user = self.context.get("user")
        event_attachment = instance.event
        if event_attachment:
            event = event_attachment.event
            if event:
                serializer = ShortEventSerializer(event, context={"user": user})
                return serializer.data
        else:
            return None

    def contact_set(self, instance):
        user = self.context.get("user")
        contact_attachment = instance.contact
        if contact_attachment:
            contact = contact_attachment.contact
            if not contact:
                return None
            serializer = ContactSerializer(contact, context={"user": user})
            return serializer.data
        else:
            return None

    @staticmethod
    def is_pinned_set(instance):
        return instance.pinned_at is not None

    def sender_data_set(self, instance):
        user = self.context.get("user")
        member = instance.sender
        serializer = MemberSerializer(member, context={"user": user})
        return serializer.data

    def pinned_by_set(self, instance):
        user = self.context.get("user")
        member = instance.pinned_by
        if not member:
            return None
        serializer = MemberSerializer(member, context={"user": user})
        return serializer.data

    def action_set(self, instance):
        if instance.type == Message.MessageTypes.SYSTEM:
            system_message = SystemMessageAction.objects.filter(message_id=instance.id).first()
            if system_message:
                serializer = SystemMessageActionSerializer(system_message, context={"user": self.context.get("user")})
                return serializer.data
            else:
                return None
        else:
            return None

    async def async_serialization(self, instance, user):
        self.context['user'] = user
        replayed_message = await sync_to_async(self.replayed_message_set)(instance)
        sender = await sync_to_async(self.sender_data_set)(instance)
        action = await sync_to_async(self.action_set)(instance)
        contact = await sync_to_async(self.contact_set)(instance)
        event = await sync_to_async(self.event_set)(instance)

        data = {
            'id': instance.id,
            'uuid': instance.uuid,
            'text': instance.text,
            'type': instance.type,
            'replayed_message': replayed_message,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
            'deleted_at': instance.deleted_at,
            'sender': sender,
            'is_pinned': instance.pinned_at is not None,
            'pinned_at': instance.pinned_at,
            'pinned_by': instance.pinned_by,
            'action': action,
            'contact': contact,
            'event': event,
        }

        return data

    def replayed_message_set(self, instance):
        user = self.context.get("user")
        if instance.replay_to:
            return MessageSerializer(instance.replay_to, context={"user": user}).data
        else:
            return None

    class Meta:
        model = Message
        fields = [
            'id',
            'uuid',
            'text',
            'type',
            'replayed_message',
            'created_at',
            'updated_at',
            'deleted_at',
            'sender',
            'is_pinned',
            'pinned_at',
            'pinned_by',
            'action',
            'contact',
            'event',
        ]