# Generated by Django 2.0.7 on 2018-08-04 01:27

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Emotion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(choices=[('MEL', 'Melancholy'), ('CLM', 'Calm'), ('HPY', 'Happy'), ('EXC', 'Excited')], db_index=True, max_length=3)),
                ('lower_bound', models.DecimalField(decimal_places=2, max_digits=3)),
                ('upper_bound', models.DecimalField(decimal_places=2, max_digits=3)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
