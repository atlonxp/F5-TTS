from django.db import models


class TTSConfiguration(models.Model):
    current_model = models.CharField(max_length=100, default="F5-TTS")
    configuration = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.current_model
