# Generated by Django 4.2.1 on 2023-06-22 09:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LittleLemonAPI', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='unit_price',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True),
        ),
    ]
