# Generated by Django 2.2.13 on 2020-07-11 02:31

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_delete_spotifyuserauth_records_on_moodyuser_delete'),
    ]

    operations = [
        migrations.AddField(
            model_name='spotifyuserauth',
            name='scopes',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=30), default=list, size=None),
        ),
    ]
