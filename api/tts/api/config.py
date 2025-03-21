from typing import Dict

from ninja import Router

from ..models.config.models import TTSConfiguration
from ..models.config.schema import TTSConfigurationOut, TTSConfigurationIn

router = Router()


@router.get("/config", response={200: TTSConfigurationOut, 500: Dict})
def get_configuration(request):
    """
    Get the current TTS configuration.
    """
    config = TTSConfiguration.objects.first()
    if not config:
        return 500, {"message": "No configuration found"}
    return config


@router.put("/config", response=TTSConfigurationOut)
def update_configuration(request, data: TTSConfigurationIn):
    """
    Update the TTS configuration.
    - Expects a JSON body with current_model and optional configuration
    """
    config = TTSConfiguration.objects.first()
    if not config:
        config = TTSConfiguration.objects.create(**data.dict())
    else:
        config.model = data.model
        config.checkpoint = data.checkpoint
        config.vocab = data.vocab
        config.config = data.config
        config.save()
    # Optionally, trigger actions such as reloading the TTS model here.
    return config
