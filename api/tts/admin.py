from django.contrib import admin
from unfold.admin import ModelAdmin

from .models.config.models import TTSConfiguration
from .models.speaker.models import Speaker
from .models.tts.models import UsageLog


@admin.register(TTSConfiguration)
class tts_config_admin(ModelAdmin):
    pass


@admin.register(Speaker)
class speaker_admin(ModelAdmin):
    pass


@admin.register(UsageLog)
class usage_log_admin(ModelAdmin):
    pass
