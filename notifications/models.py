from django.utils.translation import gettext_lazy as _

from django.db import models

from events.models import Event
from users.models import User, Contact


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        COMMON = "Common", _("Common")
        EVENT = "Event", _("Event")
        CONTACT = "Contact", _("Contact")

    notification_type = models.CharField(
        verbose_name='Notification type',
        choices=NotificationType.choices,
        max_length=30,
        default='Common'
    )
    user = models.ForeignKey(
        User,
        verbose_name='Notification user',
        on_delete=models.CASCADE,
    )
    event = models.ForeignKey(
        Event,
        verbose_name='Event',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Is read'
    )
    notification_contact = models.ForeignKey(
        User,
        related_name='notification_contact',
        verbose_name='Notification contact',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    notification_title = models.CharField(
        max_length=200,
        verbose_name='Notification title',
    )
    text = models.CharField(
        max_length=200,
        verbose_name='Notification text',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',
        null=True,
    )
    contact_id = models.IntegerField(
        verbose_name="contact_id",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return self.notification_title