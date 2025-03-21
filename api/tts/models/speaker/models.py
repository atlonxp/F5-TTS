import os
import uuid

import soundfile as sf
from django.db import models
from django.db.models import OneToOneField
from filer.fields.file import FilerFileField
from filer.models.filemodels import File

GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    ('KM', 'Male (Kid)'),
    ('KF', 'Female (Kid)'),
)


def get_audio_extension(file_name):
    """ Extract the file extension safely """
    return file_name.split('.')[-1] if '.' in file_name else ''


class ReferenceAudio(models.Model):
    uuid = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    text = models.TextField(blank=True)
    audio = FilerFileField(related_name='reference_audio', blank=False, null=True, on_delete=models.SET_NULL)
    duration = models.FloatField(default=0.0)

    def __str__(self):
        if self.audio:
            return self.audio.original_filename
        return str(self.uuid)

    def save(self, *args, **kwargs):
        if self.audio and self.audio.file:
            file_extension = get_audio_extension(self.audio.original_filename)
            new_path = os.path.join('speakers/', str(self.uuid)[:2], str(self.uuid)[2:4],
                                    f"{self.uuid}.{file_extension}")
            self.audio.file.storage.save(new_path, self.audio.file)

            # Update the Filer File model to reflect the new path
            file_obj = File.objects.get(pk=self.audio.pk)
            file_obj.file.name = new_path
            file_obj.save()

            # Ensure `self.audio.file.name` is updated properly
            self.audio.file.name = new_path

            # Compute and update audio duration
            audio_path = self.audio.file.path  # Ensure the correct path is used
            if os.path.exists(audio_path):
                with sf.SoundFile(audio_path) as f:
                    self.duration = len(f) / f.samplerate

        super().save(*args, **kwargs)


class Speaker(models.Model):
    DEFAULT_GENDER = 'M'
    DEFAULT_LANGUAGE = 'th'

    speaker_id = models.CharField(max_length=128, blank=True, null=True)
    name = models.CharField(max_length=100, unique=True)
    reference = OneToOneField(ReferenceAudio, on_delete=models.SET_NULL, null=True)

    default = models.BooleanField(default=False)
    default_speed = models.FloatField(default=1.0)

    gender = models.CharField(max_length=3, choices=GENDER_CHOICES, default=DEFAULT_GENDER)
    language = models.CharField(max_length=128, default=DEFAULT_LANGUAGE)

    def __str__(self):
        return f"{self.name} ({self.gender} - {self.language})"

    def save(self, *args, **kwargs):
        # Update default speaker
        if self.default:
            Speaker.objects.exclude(pk=self.pk).update(default=False)
        if self.reference:
            # force save reference audio in order to get duration and reorganize file path
            self.reference.save()
        # Set speaker ID
        last_speaker = Speaker.objects.filter(gender=self.gender).order_by('-id').first()
        i = int(last_speaker.speaker_id[-2:]) + 1 if last_speaker else 1
        speaker_id = f"{self.gender}{i:02d}"
        self.speaker_id = speaker_id
        super().save(*args, **kwargs)

    @staticmethod
    def get_default_speaker():
        return Speaker.objects.filter(default=True).first()

    @staticmethod
    def rerun_speaker_duration():
        for speaker in Speaker.objects.all():
            speaker.save()
        return True

    @staticmethod
    def rerun_speaker_id():
        """
        Re-run speaker id to start from 1 and increment by 1.
        Format is based on the following criteria:
        - Gender: M, F, KM, KF
        - Language: th, en
        - Speaker ID: 1, 2, 3, ...
        Examples:
        - M01, M02, M03, ...
        - F01, F02, F03, ...
        - KM01, KM02, KM03, ...
        - KF01, KF02, KF03, ...
        Returns:
        """
        for gender in GENDER_CHOICES:
            speakers = Speaker.objects.filter(gender=gender[0])
            for i, speaker in enumerate(speakers, start=1):
                speaker_id = f"{speaker.gender}{i:02d}"
                speaker.speaker_id = speaker_id
                speaker.save()
