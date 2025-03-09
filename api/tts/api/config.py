from ninja import Router

from ..models.config.models import TTSConfiguration
from ..models.config.schema import TTSConfigurationOut, TTSConfigurationIn

router = Router()


@router.get("/config", response=TTSConfigurationOut)
def get_configuration(request):
    """
    Get the current TTS configuration.
    """
    config = TTSConfiguration.objects.first()
    if not config:
        config = TTSConfiguration.objects.create(current_model="F5-TTS", configuration={})
    return config


@router.put("/config", response=TTSConfigurationOut)
def update_configuration(request, data: TTSConfigurationIn):
    """
    Update the TTS configuration.
    - Expects a JSON body with current_model and optional configuration
    """
    config = TTSConfiguration.objects.first()
    if not config:
        config = TTSConfiguration.objects.create(current_model=data.current_model, configuration=data.configuration)
    else:
        config.current_model = data.current_model
        config.configuration = data.configuration
        config.save()
    # Optionally, trigger actions such as reloading the TTS model here.
    return config
