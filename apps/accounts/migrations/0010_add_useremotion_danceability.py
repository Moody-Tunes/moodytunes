# Generated by Django 2.2.10 on 2020-04-18 04:10

import base.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_remove_prefetch_manager'),
    ]

    operations = [
        migrations.AddField(
            model_name='useremotion',
            name='danceability',
            field=models.FloatField(default=0, validators=[base.validators.validate_decimal_value]),
        ),
    ]