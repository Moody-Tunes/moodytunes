# Generated by Django 2.2.10 on 2020-04-18 02:13

import base.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tunes', '0004_add_song_genre'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='danceability',
            field=models.FloatField(default=0, validators=[base.validators.validate_decimal_value]),
        ),
    ]
