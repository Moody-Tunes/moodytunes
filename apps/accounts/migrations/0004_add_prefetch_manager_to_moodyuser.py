# Generated by Django 2.1.2 on 2019-01-11 02:32

import django.contrib.auth.models
from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_add_unique_together_on_user_emotion'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='moodyuser',
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
