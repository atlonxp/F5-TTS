from django.db import models
import soundfile as sf
import os

from filer.fields.file import FilerFileField


class Speaker(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('KM', 'Male (Kid)'),
        ('KF', 'Female (Kid)'),
    )
    DEFAULT_GENDER = 'M'
    DEFAULT_LANGUAGE = 'th'

    name = models.CharField(max_length=100, unique=True)
    reference_text = models.TextField(blank=True)
    reference_audio = FilerFileField(related_name='reference_audio', blank=False, null=True, on_delete=models.SET_NULL)
    duration = models.FloatField(default=0.0)

    is_default_speaker = models.BooleanField(default=False)
    default_speed = models.FloatField(default=1.0)

    gender = models.CharField(max_length=3, choices=GENDER_CHOICES, default=DEFAULT_GENDER)
    language = models.CharField(max_length=128, default=DEFAULT_LANGUAGE)

    def __str__(self):
        return f"{self.name} ({self.gender})"

    def save(self, *args, **kwargs):
        # Update default speaker
        if self.is_default_speaker:
            Speaker.objects.exclude(pk=self.pk).update(is_default_speaker=False)

        # Get duration of the audio
        if self.reference_audio:
            audio_path = self.reference_audio.path
            if os.path.exists(audio_path):
                with sf.SoundFile(audio_path) as f:
                    self.duration = len(f) / f.samplerate
        super().save(*args, **kwargs)