# Generated by Django 2.2.13 on 2020-07-03 01:47

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_make_spotify_auth_one_to_one_on_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpotifyUserData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('top_artists', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=200), default=list, size=None)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='spotifyuserauth',
            name='spotify_data',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.SpotifyUserData'),
        ),
    ]