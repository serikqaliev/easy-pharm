from django.db import models


class Timezone(models.Model):
    name = models.CharField(
      max_length=250,
      verbose_name='Название',
    )
    value = models.CharField(
      max_length=250,
      verbose_name='Значение',
    )

    class Meta:
        verbose_name = 'Часовой пояс'
        verbose_name_plural = 'Часовые пояса'

    def __str__(self):
        return self.name


class Countrycode(models.Model):
    name = models.CharField(
      max_length=250,
      verbose_name='Название',
    )
    dial_code = models.CharField(
      max_length=7,
      verbose_name='Код телефона',
    )
    code = models.CharField(
      max_length=4,
      verbose_name='Код страны',
    )
    flag = models.CharField(
      max_length=100,
      verbose_name='Флаг',
      null=True,
      blank=True
    )

    class Meta:
        verbose_name = 'Телефонный код'
        verbose_name_plural = 'Телефонные коды'

    def __str__(self):
        return self.name

# Create your models here.
