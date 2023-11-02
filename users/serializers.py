from rest_framework import serializers

from chat.models import Chat, Member
from users.models import User, Contact, Privacy, Settings, UserRelations
from users.utils.privacy_settings import get_user_avatar


class ContactSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField('contact_type_set', read_only=True)
    contact_data = serializers.SerializerMethodField('contact_set', read_only=True)
    user_data = serializers.SerializerMethodField('user_set', read_only=True)

    @staticmethod
    def contact_type_set(instance):
        if instance.in_calendaria:
            return 'IN_CALENDARIA'
        return 'NOT_IN_CALENDARIA'

    def user_set(self, instance):
        user = User.objects.filter(phone=instance.phone).first()

        if user:
            return {
                'id': user.id,
                'username': user.username,
                'phone': user.phone,
                'avatar': get_user_avatar(user, self.context.get("user")),
                'is_online': user.is_online,
                'last_seen': user.last_online,
            }
        else:
            return None

    @staticmethod
    def contact_set(instance):
        return {
            'id': instance.id,
            'label': instance.label,
            'phone': instance.phone,
        }

    class Meta:
        model = Contact
        fields = [
            'type',
            'contact_data',
            'user_data',
        ]


class PrivacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Privacy
        fields = [
            "last_actions",
            "profile_image",
            "group_chat_invite",
            "event_invite",
            "my_events",
        ]


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = [
            "theme"
        ]


class ShortUserSerializer(serializers.ModelSerializer):
    user_data = serializers.SerializerMethodField('user_set', read_only=True)
    contact_data = serializers.SerializerMethodField('contact_set', read_only=True)

    def user_set(self, instance):
        user = self.context.get("user")
        avatar = get_user_avatar(instance, user)

        return {
            'id': instance.id,
            'username': instance.username,
            'phone': instance.phone,
            'avatar': avatar,
            'is_online': instance.is_online,
            'last_seen': self.last_seen_set(instance),
            'is_me': instance.id == user.id,
        }

    @staticmethod
    def last_seen_set(instance):
        if instance.is_online:
            return None
        return instance.last_online

    def contact_set(self, instance):
        user = self.context.get("user")
        contact = Contact.objects.filter(phone=instance.phone, user=user).first()
        if contact:
            return {
                'id': contact.id,
                'label': contact.label,
                'phone': contact.phone,
            }
        else:
            return None

    class Meta:
        model = User
        fields = [
            'user_data',
            'contact_data',
        ]


class ProfileUserSerializer(serializers.ModelSerializer):
    contact_data = serializers.SerializerMethodField('contact_set', read_only=True)
    user_data = serializers.SerializerMethodField('user_set', read_only=True)
    privacy = serializers.SerializerMethodField('privacy_set', read_only=True)
    relation_settings = serializers.SerializerMethodField('relation_settings_set', read_only=True)

    def contact_set(self, instance):
        user = self.context.get("user")
        contact = Contact.objects.filter(phone=instance.phone, user=user).first()
        if contact:
            return {
                'id': contact.id,
                'label': contact.label,
                'phone': contact.phone,
            }
        else:
            return None

    def user_set(self, instance):
        privacy_settings = Privacy.objects.filter(user=instance).first()
        profile_image_visibility = privacy_settings.profile_image if privacy_settings else None
        avatar = instance.avatar.url if instance.avatar else None

        if not profile_image_visibility:
            avatar = avatar

        if profile_image_visibility == 'All' or profile_image_visibility:
            avatar = avatar
        elif profile_image_visibility == 'My Contacts':
            # TODO: check if user is in contacts
            requested_user = self.context.get("user")
            contact = Contact.objects.filter(phone=instance.phone, user=requested_user).first()
            if contact:
                avatar = avatar
            else:
                avatar = None

        chat = Chat.objects.filter(member__user=instance, chat_type=Chat.ChatTypes.DIRECT) \
            .filter(member__user=self.context.get("user")).first()

        return {
            'id': instance.id,
            'username': instance.username,
            'phone': instance.phone,
            'avatar': avatar,
            'chat_id': chat.id if chat else None,
            'status': instance.status,
            'status_change_at': instance.status_change_at,
            'is_online': instance.is_online,
            'last_seen': instance.last_online,
            'is_active': instance.is_active,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
        }

    def relation_settings_set(self, instance):
        user = self.context.get("user")
        relation_settings = UserRelations.objects.filter(user=user, related_user=instance).first()

        if relation_settings:
            return {
                'blocked': relation_settings.blocked,
                'blocked_description': relation_settings.blocked_desc,
                'muted': relation_settings.muted,
                'autosave_media': relation_settings.autosave_media,
            }

    @staticmethod
    def privacy_set(instance):
        privacy = Privacy.objects.filter(user=instance).first()
        serializer = PrivacySerializer(privacy)
        return serializer.data

    class Meta:
        model = User
        fields = [
            'contact_data',
            'user_data',
            'privacy',
            'relation_settings',
        ]


class UserSerializer(serializers.ModelSerializer):
    privacy = serializers.SerializerMethodField('privacy_set', read_only=True)
    settings = serializers.SerializerMethodField('settings_set', read_only=True)
    total_unread_count = serializers.SerializerMethodField('total_unread_count_set', read_only=True)
    total_unread_chats_count = serializers.SerializerMethodField('total_unread_chats_count_set', read_only=True)

    @staticmethod
    def privacy_set(instance):
        privacy = Privacy.objects.filter(user=instance).first()
        serializer = PrivacySerializer(privacy)
        return serializer.data

    @staticmethod
    def settings_set(instance):
        settings = Settings.objects.filter(user=instance).first()
        serializer = SettingsSerializer(settings)
        return serializer.data

    @staticmethod
    def total_unread_count_set(instance):
        total_unread_count = 0
        memberships = Member.objects.filter(user=instance)
        chats = Chat.objects.filter(member__in=memberships)
        for chat in chats:
            total_unread_count += memberships.get(chat=chat).unread_count()
        return total_unread_count

    @staticmethod
    def total_unread_chats_count_set(instance):
        total_unread_chats_count = 0
        memberships = Member.objects.filter(user=instance)
        chats = Chat.objects.filter(member__in=memberships)

        for chat in chats:
            if memberships.get(chat=chat).unread_count() > 0:
                total_unread_chats_count += 1

        return total_unread_chats_count

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'username',
            'phone',
            'time_zone',
            'avatar',
            'created_at',
            'updated_at',
            'status_change_at',
            'is_active',
            'is_online',
            'privacy',
            'settings',
            'status',
            'in_calendaria',
            'total_unread_count',
            'total_unread_chats_count',
        ]
