from django.db import models


class Category(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True
    )

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = 'Category of Medicine'
        verbose_name_plural = 'Categories of Medicine'
