from ninja import ModelSchema

from tts.models.speaker.models import Speaker, ReferenceAudio


class ReferenceOut(ModelSchema):
    class Meta:
        model = ReferenceAudio
        fields = ["uuid", "text", "audio", "duration"]


class SpeakerIn(ModelSchema):
    reference_text: str

    class Meta:
        model = Speaker
        fields = ["name", "gender", "language"]


class SpeakerOut(ModelSchema):
    reference: ReferenceOut

    class Meta:
        model = Speaker
        fields = ["id", "name", "gender", "speaker_id"]
