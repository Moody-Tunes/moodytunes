# Generated by Django 2.1 on 2018-08-31 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tunes', '0003_create_song_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='genre',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]
