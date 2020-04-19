# Generated by Django 2.2.10 on 2020-04-18 03:44

import json
import base.validators
from django.db import migrations, models


def update_emotion_danceability(apps, schema_editor):
    fixture_file = 'apps/tunes/fixtures/Initial_Emotions.json'
    Emotion = apps.get_model('tunes', 'Emotion')

    with open(fixture_file) as fp:
        emotions = json.load(fp)

    for emotion_data in emotions:
        emotion = Emotion.objects.get(pk=emotion_data['pk'])
        emotion.danceability = emotion_data['fields']['danceability']
        emotion.save()


def reset_emotion_danceability(apps, schema_editor):
    # Intentionally only reset records loaded from initial fixture
    Emotion = apps.get_model('tunes', 'Emotion')
    db_alias = schema_editor.connection.alias
    initial_emotions = [
        'MEL',
        'CLM',
        'HPY',
        'EXC',
    ]

    Emotion.objects.using(db_alias).filter(name__in=initial_emotions).update(danceability=0)


class Migration(migrations.Migration):

    dependencies = [
        ('tunes', '0005_add_song_danceability'),
    ]

    operations = [
        migrations.AddField(
            model_name='emotion',
            name='danceability',
            field=models.FloatField(default=0, validators=[base.validators.validate_decimal_value]),
        ),
        migrations.RunPython(
            update_emotion_danceability,
            reverse_code=reset_emotion_danceability
        )
    ]