from rest_framework import serializers

from .member_serializer import MemberSerializer
from .message_serializer import MessageSerializer
from users.serializers import ShortUserSerializer, ProfileUserSerializer
from chat.models import Message, Member, Chat, DeletedMessage


class ChatStateSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField('type_set', read_only=True)
    data = serializers.SerializerMethodField('data_set', read_only=True)
    membership = serializers.SerializerMethodField('membership_set', read_only=True)
    messages = serializers.SerializerMethodField('messages_set', read_only=True)
    members = serializers.SerializerMethodField('members_set', read_only=True)
    reads = serializers.SerializerMethodField('reads_set', read_only=True)
    archived_at = serializers.SerializerMethodField('archived_at_set', read_only=True)
    muted_at = serializers.SerializerMethodField('muted_at_set', read_only=True)
    pinned_at = serializers.SerializerMethodField('pinned_at_set', read_only=True)
    last_message_at = serializers.SerializerMethodField('last_message_at_set', read_only=True)
    created_at = serializers.SerializerMethodField('created_at_set', read_only=True)
    created_by = serializers.SerializerMethodField('created_by_set', read_only=True)
    truncated_at = serializers.SerializerMethodField('truncated_at_set', read_only=True)
    updated_at = serializers.SerializerMethodField('updated_at_set', read_only=True)
    deleted_at = serializers.SerializerMethodField('deleted_at_set', read_only=True)

    def muted_at_set(self, instance):
        member = Member.objects.filter(chat=instance, user=self.context.get("user")).first()
        if member:
            return member.muted_at.isoformat() if member.muted_at else None
        return None

    def pinned_at_set(self, instance):
        member = Member.objects.filter(chat=instance, user=self.context.get("user")).first()
        if member:
            return member.pinned_at.isoformat() if member.pinned_at else None
        return None

    def last_message_at_set(self, instance):
        return instance.last_message_sent_at(self.context.get("user")).isoformat() if instance.last_message_sent_at(self.context.get("user")) else None

    def truncated_at_set(self, instance):
        member = Member.objects.filter(chat=instance, user=self.context.get("user")).first()
        if member:
            return member.truncated_at.isoformat() if member.truncated_at else None
        return None

    @staticmethod
    def created_at_set(instance):
        return instance.created_at.isoformat() if instance.created_at else None

    def created_by_set(self, instance):
        member = Member.objects.filter(chat=instance, user=self.context.get("user")).first()
        return MemberSerializer(member, context={"user": self.context.get("user")}).data if member else None

    @staticmethod
    def updated_at_set(instance):
        return instance.updated_at.isoformat() if instance.updated_at else None

    @staticmethod
    def deleted_at_set(instance):
        return instance.deleted_at.isoformat() if instance.deleted_at else None

    def archived_at_set(self, instance):
        member = Member.objects.filter(chat=instance, user=self.context.get("user")).first()
        if member:
            return member.archived_at.isoformat() if member.archived_at else None
        return None

    @staticmethod
    def type_set(instance):
        return instance.chat_type

    def data_set(self, instance):
        user = self.context.get("user")
        last_message_sent_at = instance.last_message_sent_at(user)
        last_message_sent_at_iso = last_message_sent_at.isoformat() if last_message_sent_at else None

        if instance.chat_type == 'direct':
            member = Member.objects.filter(chat=instance).exclude(user=user).first()
            serializer = ProfileUserSerializer(member.user, context={"user": user})

            return {
                'id': instance.id,
                'type': 'direct',
                'user': serializer.data,
            }
        elif instance.chat_type == 'group':
            cover_image_url = None
            if instance.cover_image:
                cover_image_url = instance.cover_image.url

            members_count = Member.objects.filter(chat=instance).count()

            return {
                'id': instance.id,
                'type': 'group',
                'title': instance.title,
                'cover_image': cover_image_url,
                'description': instance.description,
                'members_count': members_count,
            }
        elif instance.chat_type == 'event':
            event = instance.event
            cover_image_url = None
            if event.cover_image and event.cover_image != 'None':
                cover_image_url = event.cover_image.url

            members_count = Member.objects.filter(chat=instance).count()

            return {
                'id': instance.id,
                'event_id': event.id,
                'type': 'event',
                'title': event.title,
                'cover_image': cover_image_url,
                'description': event.description,
                'start_date_time': event.start_date_time,
                'end_date_time': event.end_date_time,
                'members_count': members_count,
            }

    def membership_set(self, instance):
        user = self.context.get("user")
        member = Member.objects.filter(chat=instance, user=user).first()
        if not member:
            return None
        serializer = MemberSerializer(member, context={"user": self.context.get("user")})
        return serializer.data

    def messages_set(self, instance):
        without_messages = self.context.get("without_messages")
        if without_messages:
            return []
        deleted_messages = DeletedMessage.objects.filter(message__chat=instance, member__user=self.context.get("user"))
        messages = Message.objects.filter(chat=instance).exclude(id__in=deleted_messages.values('message_id')).order_by('created_at')[:50]
        print('messages:::', len(messages))
        serializer = MessageSerializer(messages, many=True, context={"user": self.context.get("user")})
        return serializer.data

    def members_set(self, instance):
        without_members = self.context.get("without_members")
        if without_members:
            return []
        members = Member.objects.filter(chat=instance, status='Active')
        serializer = MemberSerializer(members, many=True, context={"user": self.context.get("user")})
        return serializer.data

    def reads_set(self, instance):
        user = self.context.get("user")
        members = Member.objects.filter(chat=instance, status='Active')
        serializer = ChatReadSerializer(members, many=True, context={"user": user})
        return serializer.data

    class Meta:
        model = Chat
        fields = [
            'type',
            'data',
            'membership',
            'messages',
            'members',
            'reads',
            'archived_at',
            'muted_at',
            'pinned_at',
            'last_message_at',
            'created_at',
            'created_by',
            'truncated_at',
            'updated_at',
            'deleted_at',
        ]


class ChatReadSerializer(serializers.ModelSerializer):
    member = serializers.SerializerMethodField('member_set', read_only=True)
    unread_count = serializers.SerializerMethodField('unread_count_set', read_only=True)
    last_read_at = serializers.SerializerMethodField('last_read_at_set', read_only=True)

    def member_set(self, instance):
        serialized = MemberSerializer(instance, context={"user": self.context.get("user")})
        return serialized.data

    @staticmethod
    def unread_count_set(instance):
        return instance.unread_count()

    @staticmethod
    def last_read_at_set(instance):
        return instance.last_read_at.isoformat() if instance.last_read_at else None

    class Meta:
        model = Member
        fields = [
            'member',
            'last_read_at',
            'unread_count',
        ]


class ChatSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField('message_set', read_only=True)

    @staticmethod
    def message_set(instance):
        message = Message.objects.filter(chat=instance).order_by('-created_at')[:50]
        serializer = MessageSerializer(message, many=True)
        return serializer.data

    class Meta:
        model = Chat
        fields = [
            'messages'
        ]
