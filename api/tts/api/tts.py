from typing import Dict

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.urls import reverse
from filer.models.filemodels import File as FilerFile
from ninja import Router, UploadedFile, File, Form

from ..models.speaker.models import Speaker, ReferenceAudio
from ..models.tts.models import UsageLog, save_filer_file
from ..models.tts.schema import GenerateTTSOutput, GenerateTTSInput, GenerateCustomTTSInput

router = Router()

domain = "https://a100.ap.ngrok.io"


@router.post("/generate", response={200: GenerateTTSOutput, 400: Dict, 500: Dict})
def generate(request, data: GenerateTTSInput):
    """
    Generates speech using F5-TTS.
    - Expects a JSON body with prompt_text and speaker_id.
    """
    # Validate speaker_id against database
    try:
        speaker = Speaker.objects.get(speaker_id=data.speaker_id)
    except Speaker.DoesNotExist:
        return 400, {
            "message": f"Invalid speaker_id '{data.speaker_id}'. Must be one of: {list(Speaker.objects.values_list('speaker_id', flat=True))}"}

    try:
        from ..infer_gradio_api import basic_tts
        audio, spectrogram, _, enhanced_audio = basic_tts(
            ref_audio_input=speaker.reference.audio.file.path,
            ref_text_input=speaker.reference.text,
            gen_text_input=data.prompt_text,
            remove_silence=False,
            cross_fade_duration_slider=0.15,
            nfe_slider=32,
            speed_slider=1,
            verbose=False
        )

        usage_log = UsageLog.objects.create(
            speaker=speaker,
            custom_reference=None,
            generated_text=data.prompt_text,
            generated_audio=save_filer_file(audio, folder="tts_generated"),
            enhanced_audio=save_filer_file(enhanced_audio, folder="tts_generated"),
            spectrogram=save_filer_file(spectrogram, folder="tts_spectrograms"),
        )

        return GenerateTTSOutput(
            message="TTS generated successfully",
            audio=domain + usage_log.generated_audio.url,
            enhanced_audio=domain + usage_log.enhanced_audio.url,
            spectrogram=domain + usage_log.spectrogram.url,
            usage_log_id=usage_log.id,
            usage_log_url=domain + reverse('admin:tts_usagelog_change', args=(usage_log.id,))
        )
    except Exception as e:
        return 500, {"message": str(e)}


@router.post("/generate_vc", response=GenerateTTSOutput)
def generate_with_reference(request, data: Form[GenerateCustomTTSInput], reference_audio: UploadedFile = File(...)):
    """
    Generates speech with Custom Reference using F5-TTS.
    - Expects a JSON body with prompt_text, reference_text, and reference_audio.
    """
    # Save the uploaded reference_audio file and create ReferenceAudio instance
    relative_path = default_storage.save(f"speakers/{reference_audio.name}", ContentFile(reference_audio.read()))
    absolute_path = default_storage.path(relative_path)
    with open(absolute_path, "rb") as f:
        django_file = ContentFile(f.read(), name=relative_path)
        filer_file = FilerFile.objects.create(
            original_filename=reference_audio.name,
            file=django_file
        )
    reference = ReferenceAudio.objects.create(text=data.reference_text, audio=filer_file)

    try:
        from ..infer_gradio_api import basic_tts
        audio, spectrogram, _, enhanced_audio = basic_tts(
            ref_audio_input=reference.audio.file.path,
            ref_text_input=reference.text,
            gen_text_input=data.prompt_text,
            remove_silence=False,
            cross_fade_duration_slider=0.15,
            nfe_slider=32,
            speed_slider=1,
            verbose=False
        )

        usage_log = UsageLog.objects.create(
            speaker=None,
            custom_reference=reference,
            generated_text=data.prompt_text,
            generated_audio=save_filer_file(audio, folder="tts_generated"),
            enhanced_audio=save_filer_file(enhanced_audio, folder="tts_generated"),
            spectrogram=save_filer_file(spectrogram, folder="tts_spectrograms"),
        )

        return GenerateTTSOutput(
            message="TTS generated successfully",
            audio=domain + usage_log.generated_audio.url,
            enhanced_audio=domain + usage_log.enhanced_audio.url,
            spectrogram=domain + usage_log.spectrogram.url,
            usage_log_id=usage_log.id,
            usage_log_url=domain + reverse('admin:tts_usagelog_change', args=(usage_log.id,))
        )
    except Exception as e:
        return 500, {"message": str(e)}
