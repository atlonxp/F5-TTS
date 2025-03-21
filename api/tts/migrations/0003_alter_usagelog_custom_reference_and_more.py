# Generated by Django 5.1.7 on 2025-03-10 07:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('tts', '0002_usagelog_spectrogram_alter_usagelog_enhanced_audio_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usagelog',
            name='custom_reference',
            field=models.OneToOneField(default=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                       to='tts.referenceaudio'),
        ),
        migrations.AlterField(
            model_name='usagelog',
            name='speaker',
            field=models.OneToOneField(default=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                       to='tts.speaker'),
        ),
    ]
