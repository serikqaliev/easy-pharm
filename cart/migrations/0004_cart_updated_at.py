# Generated by Django 4.2.4 on 2023-11-12 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0003_alter_cart_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
