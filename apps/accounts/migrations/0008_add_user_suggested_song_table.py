# Generated by Django 2.1.9 on 2019-06-18 21:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_create_spotify_user_auth_table'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSuggestedSong',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(db_index=True, max_length=36, unique=True)),
                ('processed', models.BooleanField(db_index=True, default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('unprocessed_suggestions', django.db.models.manager.Manager()),
            ],
        ),
    ]
