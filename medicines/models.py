from django.db import models


class Medicine(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='media/medicine')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} - {self.price}'

    class Meta:
        verbose_name = 'Medicine'
        verbose_name_plural = 'Medicines'


class Symptom(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    medicines = models.ManyToManyField(Medicine, related_name='symptoms')

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = 'Symptom'
        verbose_name_plural = 'Symptoms'
