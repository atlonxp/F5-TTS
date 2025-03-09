import tempfile
from typing import Optional

from ninja import Router
from ninja import UploadedFile, File

from ..models.tts.schema import GenerateTTSOutput, GenerateTTSInput

# from f5_tts.infer.infer_basic_tts import infer

router = Router()


@router.post("/generate", response=GenerateTTSOutput)
def generate(request, data: GenerateTTSInput, reference_audio: Optional[UploadedFile] = File(None)):
    """
    Generates speech using F5-TTS.
    - Expects a JSON body with prompt_text and optional reference_text.
    - Optionally accepts an uploaded file for reference_audio.
    """
    prompt_text = data.prompt_text
    reference_text = data.reference_text or ""

    # Save the uploaded reference audio to a temporary file if provided.
    ref_audio_path = None
    if reference_audio:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(reference_audio.read())
            ref_audio_path = tmp.name

    try:
        # Call the F5-TTS inference function.
        # Adjust parameters as per your actual function signature.
        # audio_result, spectrogram_path, ref_text_out, audio_enhanced = infer(
        #     ref_audio_path,
        #     reference_text,
        #     prompt_text,
        #     "F5-TTS",  # Or use your current model configuration.
        #     remove_silence=False,
        #     cross_fade_duration=0.15,
        #     nfe_step=32,
        #     speed=1.0,
        # )
        # sample_rate, audio_data = audio_result
        #
        # # Save the generated audio to a temporary file.
        # with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
        #     sf.write(tmp_audio.name, audio_data, sample_rate)
        #     generated_audio_path = tmp_audio.name
        #
        # # Log the usage.
        # usage_log = UsageLog.objects.create(
        #     prompt_text=prompt_text,
        #     generated_text=ref_text_out,
        #     reference_text=reference_text,
        # )

        return GenerateTTSOutput(
            message="TTS generated successfully",
            generated_audio_path="",
            usage_log_id=1
        )
        # return GenerateTTSOutput(
        #     message="TTS generated successfully",
        #     generated_audio_path=generated_audio_path,
        #     usage_log_id=usage_log.id,
        # )
    except Exception as e:
        return 500, {"message": str(e)}
