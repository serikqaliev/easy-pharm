from datetime import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _

from cart.models import Cart
from users.models import User


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("PENDING")
        DELIVERED = "DELIVERED", _("DELIVERED")
        CANCELED_BY_USER = "CANCELED_BY_USER", _("CANCELED_BY_USER")
        CANCELED_BY_ADMIN = "CANCELED_BY_ADMIN", _("CANCELED_BY_ADMIN")

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.TextField(
        help_text='Address of user to deliver medicine'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    order_items = models.ManyToManyField(Cart)

    created_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.TextField(null=True, blank=True)

    def cancel_by_user(self, reason):
        self.status = self.Status.CANCELED_BY_USER
        self.canceled_at = datetime.now()
        self.cancel_reason = reason
        self.save()

    def cancel_by_admin(self, reason):
        self.status = self.Status.CANCELED_BY_ADMIN
        self.canceled_at = datetime.now()
        self.cancel_reason = reason
        self.save()

    def deliver(self):
        self.status = self.Status.DELIVERED
        self.delivered_at = datetime.now()
        self.save()

    def __str__(self):
        return f'{self.user.username} - {self.created_at}'

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
