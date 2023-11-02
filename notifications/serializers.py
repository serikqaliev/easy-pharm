from rest_framework import serializers

from events.serializers import ShortEventSerializer
from notifications.models import Notification
from users.serializers import ShortUserSerializer


class ShortNotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = [
            'id',
            'text',
            'created_at'
        ]


class ShortContactNotificationSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField('get_user_id', read_only=True)
    title = serializers.SerializerMethodField('get_title', read_only=True)
    body = serializers.SerializerMethodField('get_body', read_only=True)
    unread_count = serializers.SerializerMethodField('get_unread_count', read_only=True)

    @staticmethod
    def get_user_id(instance):
        return instance.notification_contact.id

    @staticmethod
    def get_title(instance):
        return instance.notification_title

    @staticmethod
    def get_body(instance):
        return instance.text

    @staticmethod
    def get_unread_count(instance):
        return Notification.objects.filter(
            notification_type="Contact",
            is_read=False
        ).count()

    class Meta:
        model = Notification
        fields = [
            'id',
            'user_id',
            'title',
            'body',
            'unread_count'
        ]


class ShortEventNotificationSerializer(serializers.ModelSerializer):
    event_id = serializers.SerializerMethodField('get_event_id', read_only=True)
    event_title = serializers.SerializerMethodField('get_event_title', read_only=True)
    title = serializers.SerializerMethodField('get_title', read_only=True)
    body = serializers.SerializerMethodField('get_body', read_only=True)
    unread_count = serializers.SerializerMethodField('get_unread_count', read_only=True)

    @staticmethod
    def get_event_id(instance):
        return instance.event.id

    @staticmethod
    def get_event_title(instance):
        return instance.event.title

    @staticmethod
    def get_title(instance):
        return instance.notification_title

    @staticmethod
    def get_body(instance):
        return instance.text

    @staticmethod
    def get_unread_count(instance):
        return Notification.objects.filter(
            notification_type="Event",
            is_read=False
        ).count()

    class Meta:
        model = Notification
        fields = [
            'id',
            'event_id',
            'event_title',
            'title',
            'body',
            'unread_count'
        ]


class ShortCommonNotificationSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField('get_title', read_only=True)
    body = serializers.SerializerMethodField('get_body', read_only=True)
    unread_count = serializers.SerializerMethodField('get_unread_count', read_only=True)

    @staticmethod
    def get_title(instance):
        return instance.notification_title

    @staticmethod
    def get_body(instance):
        return instance.text

    @staticmethod
    def get_unread_count(instance):
        return Notification.objects.filter(
            notification_type="Common",
            is_read=False
        ).count()

    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'body',
            'unread_count'
        ]


class CommonNotificationsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = [
            'id',
            'text',
            'notification_title'
        ]


class ContactNotificationsSerializer(serializers.ModelSerializer):
    user_data = serializers.SerializerMethodField('user_data_set', read_only=True)

    def user_data_set(self, instance):
        return ShortUserSerializer(instance.notification_contact).data

    class Meta:
        model = Notification
        fields = [
            'id',
            'text',
            'notification_title',
            'user_data',
            'contact_id'
        ]


class EventNotificationsSerializer(serializers.ModelSerializer):
    event = serializers.SerializerMethodField('get_event', read_only=True)

    @staticmethod
    def get_event(instance):
        serializer = ShortEventSerializer(instance.event, context={'user': instance.user})
        return serializer.data

    class Meta:
        model = Notification
        fields = [
            'id',
            'text',
            'notification_title',
            'event',
            'is_read',
            'created_at'
        ]