# Generated by Django 2.2.13 on 2020-07-25 06:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_add_spotifyuserauth_scopes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersongvote',
            name='context',
            field=models.CharField(blank=True, choices=[('', '-----------'), ('PARTY', 'Listening to music at a party'), ('RELAX', 'Listening to music to relax'), ('WORK', 'Listening to music while working on a task'), ('EXERCISE', 'Listening to music while exercising'), ('OTHER', 'Doing something else')], max_length=10),
        ),
    ]
