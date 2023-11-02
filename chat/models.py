import re
import uuid
from datetime import datetime

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from events.models import Event
from users.models import User, Contact


class Member(models.Model):
    class Role(models.TextChoices):
        OWNER = "Owner", _("Owner")
        ADMIN = "Admin", _("Admin")
        PARTICIPANT = "Participant", _("Participant")

    class Status(models.TextChoices):
        ACTIVE = "Active", _("Active")
        KICKED = "Kicked", _("Kicked")
        LEFT = "Left", _("Left")

    role = models.CharField(
        max_length=256,
        verbose_name='Member type',
        choices=Role.choices,
        blank=True,
    )
    status = models.CharField(
        max_length=256,
        verbose_name='Member status',
        choices=Status.choices,
        blank=True,
        default='Active'
    )
    chat = models.ForeignKey(
        'Chat',
        verbose_name='Chat',
        on_delete=models.CASCADE,
    )
    last_message = models.ForeignKey(
        'Message',
        verbose_name='Last message',
        help_text='Last message which user can access (not deleted for all, not deleted for user)',
        on_delete=models.CASCADE,
        related_name='member_last_message',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        User,
        verbose_name='User',
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',
        null=True,
    )
    muted_at = models.DateTimeField(
        verbose_name='Muted at',
        null=True,
        blank=True,
        help_text='If not null this user muted this chat'
    )
    kicked_at = models.DateTimeField(
        verbose_name='Kicked at',
        null=True,
        blank=True,
    )
    left_at = models.DateTimeField(
        verbose_name='Left at',
        null=True,
        blank=True
    )
    archived_at = models.DateTimeField(
        verbose_name='Archived at',
        null=True,
        blank=True
    )
    pinned_at = models.DateTimeField(
        verbose_name='Pinned at',
        null=True,
        blank=True
    )
    truncated_at = models.DateTimeField(
        verbose_name='Truncated at',
        null=True,
        blank=True
    )
    deleted_at = models.DateTimeField(
        verbose_name='Deleted at',
        null=True,
        blank=True
    )
    last_read_at = models.DateTimeField(
        verbose_name='Last read at',
        null=True,
        blank=True,
        default=datetime.now
    )

    def unread_count(self):
        deleted_messages_ids = DeletedMessage.objects.filter(
            member=self,
            message__chat=self.chat,
        ).values_list('message_id', flat=True)

        messages = self.chat.messages.filter(
            deleted_at__isnull=True
        ).order_by('-created_at')

        if deleted_messages_ids:
            messages = messages.exclude(
                id__in=deleted_messages_ids
            )

        last_message = messages.first()

        last_message_created_at = None
        if last_message:
            last_message_created_at = last_message.created_at

        last_read_at = self.last_read_at

        if last_read_at is None:
            return messages.count()
        else:
            if last_message_created_at is None:
                return 0
            if last_message_created_at > last_read_at:
                return messages.filter(
                    created_at__gt=last_read_at
                ).count()
            else:
                return 0

    class Meta:
        verbose_name = 'Member'
        verbose_name_plural = 'Members'
        unique_together = ["chat", "user"]

    def __str__(self):
        return str(self.id)


class Chat(models.Model):
    class ChatTypes(models.TextChoices):
        DIRECT = "direct", _("direct")
        GROUP = "group", _("group")
        EVENT = "event", _("event")

    chat_type = models.CharField(
        max_length=256,
        verbose_name='Type of chat',
        choices=ChatTypes.choices,
    )
    title = models.CharField(
        max_length=256,
        verbose_name='Title of chat',
        help_text='For direct chat - null, for group chat - title of group, for event chat - null (title of event)',
        null=True,
        blank=True
    )
    description = models.CharField(
        max_length=900,
        verbose_name='Description of chat',
        help_text='For direct chat - null, for group chat - description of group, for event chat - null (description '
                  'of event)',
        null=True,
        blank=True
    )
    cover_image = models.ImageField(
        verbose_name='Cover image',
        help_text='For direct chat - null, for group chat - cover image of group, for event chat - null (cover image '
                  'of event)',
        upload_to="chat/covers",
        null=True,
        blank=True
    )
    event = models.ForeignKey(
        Event,
        verbose_name='Event',
        on_delete=models.CASCADE,
        help_text='For direct chat - null, for group chat - null, for event chat - event',
        null=True,
        blank=True
    )
    last_message = models.ForeignKey(
        'Message',
        verbose_name='Last message',
        on_delete=models.CASCADE,
        related_name='chat_last_message',
        null=True,
        blank=True
    )
    pinned_message = models.ForeignKey(
        'Message',
        verbose_name='Pinned message',
        on_delete=models.CASCADE,
        related_name='chat_pinned_message',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',
        null=True,
    )
    created_by = models.ForeignKey(
        User,
        verbose_name='Created by',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at',
        null=True,
    )
    deleted_at = models.DateTimeField(
        verbose_name='Deleted at',
        null=True,
        blank=True
    )

    def last_message_sent_at(self, user):
        messages = Message.objects.filter(chat=self, deleted_at__isnull=True).order_by('-created_at')
        deleted_messages_ids = DeletedMessage.objects.filter(
            member__user=user,
            message__chat=self,
        ).values_list('message_id', flat=True)

        if deleted_messages_ids:
            messages = messages.exclude(
                id__in=deleted_messages_ids
            )

        last_message = messages.first()

        if last_message:
            return last_message.created_at
        else:
            return None

    def unread_count_messages(self, user):
        count = 0
        member = Member.objects.filter(chat=self, user=user).first()
        messages = Message.objects.filter(chat=self, deleted_at__isnull=True).order_by('-created_at')
        if member:
            last_read_at = member.last_read_at
            if last_read_at:
                for message in messages:
                    if message.created_at > last_read_at:
                        count += 1
                    else:
                        break

    def unread_chats_count(self, user):
        count = 0
        member = Member.objects.filter(chat=self, user=user).first()
        messages = Message.objects.filter(chat=self, deleted_at__isnull=True).order_by('-created_at')
        if member:
            last_read_at = member.last_read_at
            if last_read_at:
                for message in messages:
                    if message.created_at > last_read_at:
                        count += 1
                        continue
                    else:
                        break


    class Meta:
        verbose_name = 'Chat'
        verbose_name_plural = 'Chats'

    def __str__(self):
        return f'{self.id}'


class Message(models.Model):
    class MessageTypes(models.TextChoices):
        SYSTEM = "system", _("system")
        DEFAULT = "regular", _("regular")

    # uuid generated by client
    uuid = models.CharField(
        max_length=256,
        verbose_name='UUID of message',
        null=False,
        blank=False,
        default=uuid.uuid4
    )
    type = models.CharField(
        max_length=256,
        verbose_name='Message type',
        choices=MessageTypes.choices,
        null=True,
        blank=True,
        default='regular'
    )
    chat = models.ForeignKey(
        Chat,
        verbose_name='Chat',
        on_delete=models.CASCADE,
        related_name='messages',
    )
    text = models.CharField(
        max_length=5120,
        verbose_name='Text',
        null=True,
        blank=True
    )
    contact = models.ForeignKey(
        'ContactMessageAttachment',
        verbose_name='Contact',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    event = models.ForeignKey(
        'EventMessageAttachment',
        verbose_name='Event',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    sender = models.ForeignKey(
        Member,
        verbose_name='Member',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    pinned_at = models.DateTimeField(
        verbose_name='Pinned at',
        default=None,
        null=True,
        blank=True
    )
    pinned_by = models.ForeignKey(
        Member,
        verbose_name='Pinned by',
        on_delete=models.CASCADE,
        related_name='pinned_by',
        null=True,
        blank=True,
        default=None
    )
    replay_to = models.ForeignKey(
        'self',
        verbose_name='Replay to',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',
        null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at',
        null=True
    )
    deleted_at = models.DateTimeField(
        verbose_name='Deleted at',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return self.id


class SystemMessageAction(models.Model):
    class ActionType(models.TextChoices):
        # Every action type has a prefix 'chat' must contain chat data
        CHAT_CREATED = "chat.new", _("chat.new")
        TITLE_CHANGED = "chat.title_changed", _("chat.title_changed")
        DESCRIPTION_CHANGED = "chat.description_changed", _("chat.description_changed")
        COVER_CHANGED = "chat.cover_changed", _("chat.cover_changed")
        # Every action type has a prefix 'member' must contain member data
        MEMBER_JOINED = "member.joined", _("member.joined")
        MEMBER_ADDED = "member.added", _("member.added")
        MEMBER_LEFT = "member.left", _("member.left")
        MEMBER_KICKED = "member.kicked", _("member.kicked")
        MEMBER_ROLE_CHANGED = "member.role_changed", _("member.role_changed")
        # Every action type has a prefix 'message' must contain message data
        MESSAGE_PINNED = "message.pinned", _("message.pinned")
        MESSAGE_UNPINNED = "message.unpinned", _("message.unpinned")

    action_type = models.CharField(
        max_length=256,
        verbose_name='Action type',
        choices=ActionType.choices,
        null=True,
        blank=True
    )
    message = models.OneToOneField(
        Message,
        verbose_name='Message',
        on_delete=models.CASCADE,
    )
    # for MEMBER_ADDED, MEMBER_REMOVED, MEMBER_KICKED
    target = models.ForeignKey(
        Member,
        verbose_name='Target member',
        related_name='target_of_system_message',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    # for MESSAGE_PINNED and MESSAGE_UNPINNED
    target_message = models.ForeignKey(
        Message,
        verbose_name='Target message',
        on_delete=models.CASCADE,
        related_name='target_message_of_system_message',
        null=True,
        blank=True
    )
    target_chat = models.ForeignKey(
        Chat,
        verbose_name='Target chat',
        on_delete=models.CASCADE,
        related_name='target_chat_of_system_message',
        null=True,
        blank=True
    )
    # for TITLE_CHANGED, DESCRIPTION_CHANGED, COVER_CHANGED
    changed_from = models.CharField(
        max_length=900,
        verbose_name='Changed from',
        null=True,
        blank=True
    )
    # for TITLE_CHANGED, DESCRIPTION_CHANGED, COVER_CHANGED
    changed_to = models.CharField(
        max_length=900,
        verbose_name='Changed to',
        null=True,
        blank=True
    )

    def join_member(self, member: Member):
        self.action_type = self.ActionType.MEMBER_JOINED
        self.target = member
        self.save()

    def add_member(self, member: Member):
        self.action_type = self.ActionType.MEMBER_ADDED
        self.target = member
        self.save()

    def kick_member(self, member: Member):
        self.action_type = self.ActionType.MEMBER_KICKED
        self.target = member
        self.save()

    def left_member(self, member: Member):
        self.action_type = self.ActionType.MEMBER_LEFT
        self.target = member
        self.save()

    def change_member_role(self, member: Member, role: str):
        self.action_type = self.ActionType.MEMBER_ROLE_CHANGED
        self.target = member
        self.changed_to = role
        self.save()

    def pin_message(self, message: Message):
        self.action_type = self.ActionType.MESSAGE_PINNED
        self.target_message = message
        self.save()

    def unpin_message(self, message: Message):
        self.action_type = self.ActionType.MESSAGE_UNPINNED
        self.target_message = message
        self.save()

    def change_chat_title(self, changed_from: str, changed_to: str):
        self.action_type = self.ActionType.TITLE_CHANGED
        self.changed_from = changed_from
        self.changed_to = changed_to
        self.save()

    def change_chat_description(self, changed_from: str, changed_to: str):
        self.action_type = self.ActionType.DESCRIPTION_CHANGED
        self.changed_from = changed_from
        self.changed_to = changed_to
        self.save()

    def change_chat_cover(self, changed_from: str, changed_to: str):
        self.action_type = self.ActionType.COVER_CHANGED
        self.changed_from = changed_from
        self.changed_to = changed_to
        self.save()

    def create_chat(self, chat: Chat):
        self.action_type = self.ActionType.CHAT_CREATED
        self.target_chat = chat
        self.save()

    class Meta:
        verbose_name = 'System message action'
        verbose_name_plural = 'System message actions'

    def __str__(self):
        return self.id


class DeletedMessage(models.Model):
    message = models.ForeignKey(
        Message,
        verbose_name='Сообщение которое удалили',
        on_delete=models.CASCADE,
    )
    member = models.ForeignKey(
        Member,
        verbose_name='Пользователь который удалил сообщение',
        on_delete=models.CASCADE,
    )
    deleted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата удаления',
        null=True,
    )

    class Meta:
        verbose_name = 'Удаленное сообщение'
        verbose_name_plural = 'Удаленные сообщения'

    def __str__(self):
        return self.id


class DeletedChat(models.Model):
    chat = models.ForeignKey(
        Chat,
        verbose_name='Chat',
        on_delete=models.CASCADE,
    )
    member = models.ForeignKey(
        Member,
        verbose_name='Member',
        on_delete=models.CASCADE,
    )
    deleted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Deleted at',
        null=True,
    )

    class Meta:
        verbose_name = 'Deleted chat'
        verbose_name_plural = 'Deleted chats'

    def __str__(self):
        return self.id


class Attachment(models.Model):
    class AttachmentType(models.TextChoices):
        IMAGE = "IMAGE", _("IMAGE")
        VIDEO = "VIDEO", _("VIDEO")
        FILE = "FILE", _("FILE")

    attachment_type = models.CharField(
        max_length=256,
        verbose_name='Type of attachment',
        choices=AttachmentType.choices,
        null=False,
    )
    file = models.FileField(
        verbose_name='File',
        upload_to="chat/attachments",
        null=True,
        blank=True
    )
    message = models.ForeignKey(
        'Message',
        verbose_name='Message which contains this attachment',
        related_name='message_attachments',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    size = models.IntegerField(
        verbose_name='Size of attachment in bytes',
        null=True,
        blank=True
    )
    duration = models.IntegerField(
        verbose_name='Duration of attachment in seconds (for video)',
        null=True,
        blank=True
    )
    width = models.IntegerField(
        verbose_name='Width of attachment in pixels (for image, video)',
        null=True,
        blank=True
    )
    height = models.IntegerField(
        verbose_name='Height of attachment in pixels (for image, video)',
        null=True,
        blank=True
    )
    deleted_at = models.DateTimeField(
        verbose_name='Deleted at',
        null=True,  # if null - this attachment is not deleted
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',
        null=True,
    )

    class Meta:
        verbose_name = 'Attachment'
        verbose_name_plural = 'Attachments'


class ContactMessageAttachment(models.Model):
    contact = models.ForeignKey(
        Contact,
        verbose_name='Contact',
        on_delete=models.CASCADE,
        null=False,
    )
    user = models.ForeignKey(
        User,
        verbose_name='User',
        on_delete=models.CASCADE,
        null=True,  # if null - this contact is not registered in app
        blank=True
    )
    deleted_at = models.DateTimeField(
        verbose_name='Deleted at',
        null=True,  # if null - this attachment is not deleted
        blank=True
    )

    class Meta:
        verbose_name = 'Contact attachment'
        verbose_name_plural = 'Contact attachments'

    def __str__(self):
        return self.id


class EventMessageAttachment(models.Model):
    event = models.ForeignKey(
        Event,
        verbose_name='Event',
        on_delete=models.CASCADE,
    )
    deleted_at = models.DateTimeField(
        verbose_name='Deleted at',
        null=True,  # if null - this attachment is not deleted
        blank=True
    )

    class Meta:
        verbose_name = 'Event attachment'
        verbose_name_plural = 'Event attachments'


class LocationMessageAttachment(models.Model):
    latitude = models.FloatField(
        verbose_name='Latitude',
        null=True,
        blank=True
    )
    longitude = models.FloatField(
        verbose_name='Longitude',
        null=True,
        blank=True
    )
    address = models.CharField(
        verbose_name='Address',
        max_length=256,
        default='',
        blank=True
    )
    message = models.ForeignKey(
        'Message',
        verbose_name='Message which contains this attachment',
        related_name='message_location_attachments',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    deleted_at = models.DateTimeField(
        verbose_name='Deleted at',
        null=True,  # if null - this attachment is not deleted
        blank=True
    )

    class Meta:
        verbose_name = 'Location attachment'
        verbose_name_plural = 'Location attachments'


class Link(models.Model):
    """Each link is a part of message which parsed from text"""

    message = models.ForeignKey(
        Message,
        verbose_name='Message which contains this link',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    url = models.CharField(
        max_length=5120,
        verbose_name='URL',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Link'
        verbose_name_plural = 'Links'

    def __str__(self):
        return self.id


@receiver(post_save, sender=Message)
def default_message_post_save(sender, instance, created, **kwargs):
    if created:
        if instance.text:
            links = re.findall(r'(https?://\S+)', instance.text)
            for link in links:
                Link.objects.create(
                    chat=instance.message.chat,
                    message=instance.message,
                    url=link
                )


@receiver(post_save, sender=Message)
def message_post_save(sender, instance, created, **kwargs):
    if created:
        instance.chat.last_message = instance
        instance.chat.save()

        members = Member.objects.filter(chat=instance.chat)
        for member in members:
            if member.status == Member.Status.ACTIVE:
                member.last_message = instance
                member.save()
