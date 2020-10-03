# Generated by Django 2.2.16 on 2020-10-03 02:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tunes', '0006_add_emotion_danceability'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emotion',
            name='name',
            field=models.CharField(choices=[('MEL', 'Melancholy'), ('CLM', 'Calm'), ('HPY', 'Happy'), ('EXC', 'Excited')], max_length=3, unique=True),
        ),
    ]
