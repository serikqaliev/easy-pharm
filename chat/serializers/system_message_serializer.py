from rest_framework import serializers

from chat.models import Message, SystemMessageAction

from chat.serializers.member_serializer import MemberSerializer


class SystemMessageActionSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField('type_set', read_only=True)
    initiator = serializers.SerializerMethodField('initiator_set', read_only=True)
    message = serializers.SerializerMethodField('message_set', read_only=True)
    target = serializers.SerializerMethodField('member_set', read_only=True)
    chat = serializers.SerializerMethodField('chat_set', read_only=True)
    changed_from = serializers.SerializerMethodField('changed_from_set', read_only=True)
    changed_to = serializers.SerializerMethodField('changed_to_set', read_only=True)

    @staticmethod
    def changed_from_set(instance):
        if "changed" in instance.action_type:
            return instance.changed_from
        else:
            return None

    @staticmethod
    def changed_to_set(instance):
        if "changed" in instance.action_type:
            return instance.changed_to
        else:
            return None

    def message_set(self, instance):
        if "message" in instance.action_type:
            message = Message.objects.filter(id=instance.target_message.id).first()
            if message:
                from chat.serializers.message_serializer import MessageSerializer
                serialized = MessageSerializer(message, context={"user": self.context.get("user")})
                return serialized.data
        else:
            return None

    def member_set(self, instance):
        if "member" in instance.action_type:
            member = instance.target
            if member:
                serialized = MemberSerializer(member, context={"user": self.context.get("user")})
                return serialized.data

    def initiator_set(self, instance):
        message = instance.message
        if message:
            initiator_member = message.sender
            if initiator_member:
                serialized = MemberSerializer(initiator_member, context={"user": self.context.get("user")})
                return serialized.data

    def chat_set(self, instance):
        if "chat" in instance.action_type:
            chat = instance.target_chat
            if chat:
                from .chat_serializer import ChatStateSerializer
                serialized = ChatStateSerializer(chat, context={
                    "user": self.context.get("user"),
                    "without_messages": True,
                    "without_members": True,
                })
                return serialized.data

    @staticmethod
    def type_set(instance):
        return instance.action_type

    class Meta:
        model = SystemMessageAction
        fields = [
            'type',
            'initiator',
            'message',
            'target',
            'chat',
            'changed_from',
            'changed_to',
        ]
