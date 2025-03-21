import logging

from django.apps import AppConfig

from tts.utils import wait_for_port

logger = logging.getLogger(__name__)


class TtsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tts'
    verbose_name = 'TTS'

    # def ready(self):
    #     logger.info('Django TTS app is ready, waiting for Gradio server to start...')
    #     if not wait_for_port(55556, "0.0.0.0", timeout=60, interval=1):
    #         logger.warning("> Timeout reached. Gradio server did not start in time.")
    #     else:
    #         logger.info("> Gradio server is up!")
    #     logger.info("> Initializing TTS models...")