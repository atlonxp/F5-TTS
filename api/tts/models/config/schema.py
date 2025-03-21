from ninja import ModelSchema

from tts.models.config.models import TTSConfiguration


class TTSConfigurationIn(ModelSchema):
    class Meta:
        model = TTSConfiguration
        fields = ["model", "checkpoint", "vocab", "config"]


class TTSConfigurationOut(ModelSchema):
    class Meta:
        model = TTSConfiguration
        fields = ["model", "checkpoint", "vocab", "config"]
