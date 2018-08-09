# Generated by Django 2.0.7 on 2018-08-04 18:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tunes', '0003_create_song_table'),
        ('accounts', '0001_create_user_table'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserEmotion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('lower_bound', models.FloatField()),
                ('upper_bound', models.FloatField()),
                ('emotion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tunes.Emotion')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserSongVote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('vote', models.BooleanField()),
                ('emotion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tunes.Emotion')),
                ('song', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tunes.Song')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
