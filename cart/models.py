from django.db import models

from medicines.models import Medicine
from users.models import User


class Cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='carts'
    )
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE
    )
    quantity = models.IntegerField(
        default=1
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def add(self, medicine):
        self.medicine = medicine
        self.quantity += 1
        self.save()

    class Meta:
        unique_together = ('user', 'medicine')
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'

    def __str__(self):
        return f'{self.medicine.name} - {self.quantity}'
