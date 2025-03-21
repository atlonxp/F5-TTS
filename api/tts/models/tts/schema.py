from ninja import Schema


class GenerateTTSInput(Schema):
    prompt_text: str
    speaker_id: str


class GenerateCustomTTSInput(Schema):
    prompt_text: str
    reference_text: str


class GenerateTTSOutput(Schema):
    message: str
    audio: str
    enhanced_audio: str
    spectrogram: str
    usage_log_id: int
    usage_log_url: str
