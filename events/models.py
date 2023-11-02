import os

from django.utils.translation import gettext_lazy as _
from django.db import models

from project import settings
from users.models import User
from utils.media import generate_video_thumbnail, get_video_metadata, get_image_metadata


class Event(models.Model):
    class EventDomain(models.TextChoices):
        WORK = "Work", _("Work")
        HOME = "Home", _("Home")
        DEFAULT = "Default", _("Default")
        SHARED = "Shared", _("Shared")

    title = models.CharField(
        max_length=256,
        verbose_name='Title',
        null=True,
        blank=True
    )
    all_day = models.BooleanField(
        default=False,
        verbose_name='All day?',
        help_text='All day? (default "No")',
    )
    start_date_time = models.DateTimeField(
        verbose_name='Start date',
        null=True,
    )
    end_date_time = models.DateTimeField(
        verbose_name='End date',
        null=True,
    )
    notice_before = models.IntegerField(
        verbose_name='Notice before',
        null=True,
        blank=True
    )
    location = models.OneToOneField(
        'Location',
        verbose_name='Location',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    author = models.ForeignKey(
        User,
        verbose_name='Author',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    chat_id = models.BigIntegerField(
        verbose_name='Chat id',
        null=True,
        blank=True
    )
    type = models.CharField(
        verbose_name='Event type',
        choices=EventDomain.choices,
        max_length=30,
        default='Default'
    )
    recurrence_rule = models.CharField(
        max_length=250,
        verbose_name='Recurrence rule',
        null=True,
    )
    description = models.TextField(
        max_length=1000,
        verbose_name='Description',
        null=True,
        blank=True
    )
    cover_image = models.ImageField(
        verbose_name='Cover image',
        upload_to="event/covers/",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',
        null=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at',
        null=True,
    )

    class Meta:
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        return self.title


class Link(models.Model):
    url = models.CharField(
        max_length=256,
        verbose_name='Url',
    )
    title = models.CharField(
        max_length=256,
        verbose_name='Title',
        null=True,
        blank=True
    )
    event = models.ForeignKey(
        Event,
        verbose_name='Event',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Author of attachment',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',
        null=True,
    )

    class Meta:
        verbose_name = 'Link'
        verbose_name_plural = 'Links'

    def __str__(self):
        return self.url


class Attachment(models.Model):
    class AttachmentType(models.TextChoices):
        IMAGE = "IMAGE", _("IMAGE")
        VIDEO = "VIDEO", _("VIDEO")
        FILE = "FILE", _("FILE")

    attachment_type = models.CharField(
        verbose_name='Attachment type',
        choices=AttachmentType.choices,
        default=AttachmentType.IMAGE,
        max_length=15,
    )

    # -- Video -- #
    thumbnail = models.ImageField(
        verbose_name='Thumbnail source image',
        upload_to="event/attachments/",
        null=True,
        blank=True,
        max_length=256
    )
    duration = models.FloatField(
        verbose_name='Duration',
        null=True,
        blank=True
    )

    # -- Video/Image/File -- #
    attachment = models.FileField(
        verbose_name='Attachment',
        upload_to=f'event/attachments/',
        blank=True,
        null=True,
        max_length=256,
    )
    width = models.IntegerField(
        verbose_name='Width',
        null=True,
        blank=True
    )
    height = models.IntegerField(
        verbose_name='Height',
        null=True,
        blank=True
    )
    size = models.IntegerField(
        verbose_name='Size',
        null=True,
        blank=True
    )

    # -- Common -- #
    event = models.ForeignKey(
        Event,
        verbose_name='Event',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Author of attachment',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',
        null=True,
    )

    def _set_thumbnail_source_image(self):
        if self.attachment_type == self.AttachmentType.IMAGE:
            self.thumbnail = self.attachment.path
        elif self.attachment_type == self.AttachmentType.VIDEO:
            # create thumbnail source file
            image_path = os.path.splitext(self.attachment.path)[0] + '_thumbnail.jpg'
            generate_video_thumbnail(self.attachment.path, image_path)

            # generate path relative to media root, because this is the version that ImageField accepts
            media_image_path = os.path.relpath(image_path, settings.MEDIA_ROOT)

            self.thumbnail = media_image_path

    def _set_metadata(self):
        if self.attachment_type == self.AttachmentType.VIDEO:
            self.duration, self.width, self.height, self.size = get_video_metadata(self.attachment.path)
        elif self.attachment_type == self.AttachmentType.IMAGE:
            self.width, self.height, self.size = get_image_metadata(self.attachment.path)
        elif self.attachment_type == self.AttachmentType.FILE:
            self.size = self.attachment.size

    def clean(self):
        super(Attachment, self).clean()

    def save(self, *args, **kwargs):
        self.attachment.save(self.attachment.name, self.attachment, save=False)

        # if there is no source image
        if not bool(self.thumbnail):
            # we need to save first, for django to generate path for file in "file" field
            self._set_thumbnail_source_image()

        self._set_metadata()
        self.full_clean()

        super(Attachment, self).save(*args, **kwargs)

    # def _validate_required_fields(self, fields):
    #     print(4)
    #     for field_name in fields:
    #         if not getattr(self, field_name, None):
    #             raise ValueError(
    #                 f'{field_name.capitalize()} is required for {self.attachment_type.lower()} attachment type')

    class Meta:
        verbose_name = 'Attachment'
        verbose_name_plural = 'Attachments'

    def __str__(self):
        return self.id


class Invite(models.Model):
    class Role(models.TextChoices):
        CREATOR = "Creator", _("Creator")
        ADMIN = "Admin", _("Admin")
        DEFAULT = "Default", _("Default")

    class Status(models.TextChoices):
        WAITING = "Waiting", _("Waiting")
        MAYBE = "Maybe", _("Maybe")
        LEFT = "Left", _("Left")
        DECLINED = "Declined", _("Declined")
        ACCEPTED = "Accepted", _("Accepted")
        KICKED = "Kicked", _("Kicked")

    class Remind(models.TextChoices):
        ZERO = "0", _("0")
        FIFTEEN = "15", _("15")
        THIRTY = "30", _("30")
        SIXTY = "60", _("60")
        ONEDAY = "1440", _("1440")

    event = models.ForeignKey(
        Event,
        verbose_name='Event',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    role = models.CharField(
        verbose_name='Role',
        choices=Role.choices,
        max_length=15,
        default='Default'
    )
    user = models.ForeignKey(
        User,
        verbose_name='User',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    status = models.CharField(
        verbose_name='Invite status',
        choices=Status.choices,
        max_length=15,
        default='Waiting'
    )
    remind = models.CharField(
        verbose_name='Remind duration',
        choices=Remind.choices,
        max_length=4,
        null=False,
        blank=False,
        default=Remind.ZERO
    )
    remind_at = models.DateTimeField(
        verbose_name='Remind at',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Invite'
        verbose_name_plural = 'Invites'

    def __str__(self):
        return f'{self.id}'


class Location(models.Model):
    address = models.CharField(
        max_length=256,
        verbose_name='Address',
        null=True,
        blank=True
    )
    lng = models.FloatField(
        verbose_name='Longitude',
    )
    lat = models.FloatField(
        verbose_name='Latitude',
    )

    class Meta:
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
