from rest_framework import serializers

from events.models import Attachment, Invite, Event, Location, Link
from users.serializers import ShortUserSerializer


class EventProfileSerializer(serializers.ModelSerializer):
    event_data = serializers.SerializerMethodField('event_set', read_only=True)
    invite_data = serializers.SerializerMethodField('invite_set', read_only=True)
    members = serializers.SerializerMethodField('members_set', read_only=True)

    def event_set(self, instance):
        user = self.context.get("user")
        return EventSerializer(instance, context={"user": user}).data

    def invite_set(self, instance):
        user = self.context.get("user")
        invite = Invite.objects.filter(user=user, event=instance).first()
        if not invite:
            return None
        return InviteSerializer(invite, context={"user": user}).data

    def members_set(self, instance):
        invites = Invite.objects.filter(event=instance).order_by('role')
        return MemberSerializer(invites, many=True, context={"user": self.context.get("user")}).data

    class Meta:
        model = Event
        fields = [
            'event_data',
            'invite_data',
            'members',
        ]


class MemberSerializer(serializers.ModelSerializer):
    user_data = serializers.SerializerMethodField('user_set', read_only=True)
    invite_data = serializers.SerializerMethodField('invite_set', read_only=True)

    def user_set(self, instance):
        return ShortUserSerializer(instance.user, context={"user": self.context.get("user")}).data

    @staticmethod
    def invite_set(instance):
        return InviteSerializer(instance).data

    class Meta:
        model = Invite
        fields = [
            'user_data',
            'invite_data',
        ]


class AttachmentSerializer(serializers.ModelSerializer):
    member = serializers.SerializerMethodField('member_set', read_only=True)
    type = serializers.SerializerMethodField('get_type', read_only=True)
    attachment = serializers.SerializerMethodField('get_attachment', read_only=True)

    @staticmethod
    def get_attachment(instance):
        print(instance.attachment.path)
        return instance.attachment.url

    @staticmethod
    def get_type(instance):
        return instance.attachment_type

    def member_set(self, instance):
        invite = Invite.objects.filter(user=instance.author, event=instance.event).first()
        return MemberSerializer(invite, context={"user": self.context.get("user")}).data

    class Meta:
        model = Attachment
        fields = [
            'id',
            'attachment',
            'thumbnail',
            'type',
            'duration',
            'size',
            'width',
            'height',
            'member',
            'created_at'
        ]


class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = [
            'id',
            'role',
            'status',
            'remind',
            'remind_at',
        ]


class ShortEventSerializer(serializers.ModelSerializer):
    event_data = serializers.SerializerMethodField('event_set', read_only=True)
    invite_data = serializers.SerializerMethodField('invite_set', read_only=True)
    members = serializers.SerializerMethodField('members_set', read_only=True)

    def event_set(self, instance):
        return EventSerializer(instance, context={"user": self.context.get("user")}).data

    def invite_set(self, instance):
        user = self.context.get("user")
        invite = Invite.objects.filter(user=user, event=instance).first()

        if not invite:
            return None

        return InviteSerializer(invite).data

    @staticmethod
    def members_set(instance):
        # get all members of event
        # return list of 3 avatars and count of all members
        # order by last added, but first is creator
        members = Invite.objects.filter(
            event=instance,
            status=Invite.Status.ACCEPTED
        ).order_by('role')
        members_count = members.count()
        members = members[:3]
        members_avatars = []
        for member in members:
            if member.user.avatar:
                members_avatars.append(member.user.avatar.url)
            else:
                members_avatars.append(None)

        return {
            'members_count': members_count,
            'members_avatars': members_avatars
        }

    class Meta:
        model = Event
        fields = [
            'event_data',
            'invite_data',
            'members',
        ]


class GetInvitesSerializer(serializers.ModelSerializer):
    event_data = serializers.SerializerMethodField('event_set', read_only=True)
    event_author_data = serializers.SerializerMethodField('get_event_author_data', read_only=True)

    def event_set(self, instance):
        event = Event.objects.filter(id=instance.event.id).first()
        return ShortEventSerializer(event).data

    def get_event_author_data(self, instance):
        event = Event.objects.filter(id=instance.event.id).first()
        return ShortUserSerializer(event.author, context={"user": self.context.get("user")}).data

    class Meta:
        model = Invite
        fields = [
            'id',
            'event_author_data',
            'status',
            'remind_at',
            'role',
            'event_data'
        ]


class EventSerializer(serializers.ModelSerializer):
    event_author = serializers.SerializerMethodField('author_set', read_only=True)
    location = serializers.SerializerMethodField('get_location', read_only=True)
    chat_id = serializers.SerializerMethodField('get_chat_id', read_only=True)

    @staticmethod
    def get_chat_id(instance):
        if instance.chat_id:
            return int(instance.chat_id)
        else:
            return None

    @staticmethod
    def get_location(instance):
        if instance.location:
            return LocationSerializer(instance.location).data
        else:
            return None

    def author_set(self, instance):
        user_author = instance.author
        return ShortUserSerializer(user_author, context={"user": self.context.get("user")}).data

    class Meta:
        model = Event
        fields = [
            'id',
            'cover_image',
            'title',
            'description',
            'location',
            'all_day',
            'start_date_time',
            'end_date_time',
            'notice_before',
            'recurrence_rule',
            'chat_id',
            'type',
            'event_author',
        ]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            'id',
            'address',
            'lat',
            'lng',
        ]


class LinkSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField('member_set', read_only=True)

    def member_set(self, instance):
        invite = Invite.objects.filter(user=instance.author, event=instance.event).first()
        return MemberSerializer(invite, context={"user": self.context.get("user")}).data

    class Meta:
        model = Link
        fields = [
            'id',
            'url',
            'author',
            'created_at'
        ]
