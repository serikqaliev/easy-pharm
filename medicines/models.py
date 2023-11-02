from django.db import models

from symptoms.models import Symptom


class Medicine(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='media/medicine')
    symptoms = models.ManyToManyField(Symptom, related_name='medicines')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} - {self.price}'

    class Meta:
        verbose_name = 'Medicine'
        verbose_name_plural = 'Medicines'


