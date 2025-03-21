import os
import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models
from filer.fields.file import FilerFileField
from filer.models.filemodels import File as FilerFile

from tts.models.speaker.models import Speaker, ReferenceAudio, get_audio_extension


def save_filer_file(temp_path, folder="tts_generated"):
    """
    Saves a temporary file into Django Filer and returns a FilerFile instance.
    """
    if not temp_path or not os.path.exists(temp_path):
        return None

    # Read the file content
    with open(temp_path, "rb") as f:
        file_content = ContentFile(f.read())

    # Save the file to default storage (media folder)
    file_name = os.path.basename(temp_path)
    file_extension = get_audio_extension(file_name)
    _uuid = uuid.uuid4()
    new_path = os.path.join(f'{folder}/', str(_uuid)[:2], str(_uuid)[2:4], f"{_uuid}.{file_extension}")
    saved_path = default_storage.save(new_path, file_content)

    # Create a FilerFile instance
    filer_file = FilerFile.objects.create(
        original_filename=file_name,
        file=saved_path
    )

    return filer_file


class UsageLog(models.Model):
    generated_text = models.TextField(blank=True)
    generated_audio = FilerFileField(related_name='generated_audio', blank=False, null=True, on_delete=models.SET_NULL,
                                     editable=False)
    enhanced_audio = FilerFileField(related_name='enhanced_audio', blank=False, null=True, on_delete=models.SET_NULL,
                                    editable=False)
    spectrogram = FilerFileField(related_name='spectrogram', blank=False, null=True, on_delete=models.SET_NULL,
                                 editable=False)

    speaker = models.ForeignKey(Speaker, on_delete=models.SET_NULL, null=True, default=True, blank=True)
    custom_reference = models.ForeignKey(ReferenceAudio, on_delete=models.SET_NULL, null=True, default=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"UsageLog {self.id} at {self.timestamp}"

    def save(self, *args, **kwargs):
        if not self.pk:
            print("New instance")
            # if this is a new instance, generate TTS from admin panel
            if self.speaker:
                reference_text = self.speaker.reference.text
                reference_audio = self.speaker.reference.audio.file.path
            elif self.custom_reference:
                reference_text = self.custom_reference.text
                reference_audio = self.custom_reference.audio.file.path
            else:
                raise ValueError("UsageLog must have either a speaker or a custom reference audio")

            from tts.infer_gradio_api import basic_tts
            audio, spectrogram, _, enhanced_audio = basic_tts(
                ref_audio_input=reference_audio,
                ref_text_input=reference_text,
                gen_text_input=self.generated_text,
                remove_silence=False,
                cross_fade_duration_slider=0.15,
                nfe_slider=32,
                speed_slider=1,
                verbose=False
            )
            # Convert paths to FilerFile instances
            self.generated_audio = save_filer_file(audio, folder="tts_generated")
            self.enhanced_audio = save_filer_file(enhanced_audio, folder="tts_generated")
            self.spectrogram = save_filer_file(spectrogram, folder="tts_spectrograms")
        super().save(*args, **kwargs)
