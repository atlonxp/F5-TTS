import json
import os

from django.core.exceptions import ValidationError
from django.db import models

MODEL_DEFAULT_CONFIG = json.dumps(
    {"dim": 1024, "depth": 22, "heads": 16, "ff_mult": 2, "text_dim": 512, "conv_layers": 4}
)
MODEL_SMALL_CONFIG = json.dumps(
    {"dim": 768, "depth": 18, "heads": 12, "ff_mult": 2, "text_dim": 512, "conv_layers": 4}
)


class TTSConfiguration(models.Model):
    MODEL_CHOICES = (
        ('Custom', 'Custom'),
        ('F5-TTS', 'F5-TTS'),
    )
    DEFAULT_MODEL = MODEL_CHOICES[0][1]

    CONFIG_CHOICES = (
        (MODEL_DEFAULT_CONFIG, f'Default ({MODEL_DEFAULT_CONFIG})'),
        (MODEL_SMALL_CONFIG, f'Small ({MODEL_SMALL_CONFIG})'),
    )
    DEFAULT_CONFIG = CONFIG_CHOICES[0][1]

    model = models.CharField(max_length=256, choices=MODEL_CHOICES, default=DEFAULT_MODEL)
    checkpoint = models.CharField(max_length=256, blank=True, null=True)
    vocab = models.CharField(max_length=256, blank=True, null=True)
    config = models.JSONField(blank=True, null=True, choices=CONFIG_CHOICES, default=DEFAULT_CONFIG)

    class Meta:
        verbose_name = 'TTS Configuration'
        verbose_name_plural = 'TTS Configurations'

    def __str__(self):
        dataset, checkpoint = self.checkpoint.split(os.path.sep)[-2:]
        try:
            with open(self.vocab) as f:
                vocab_size = sum(1 for _ in f)
        except Exception:
            vocab_size = 'N/A'
        return f'{self.model} | {dataset} | {checkpoint} | Vocab size: {vocab_size}'

    def save(self, *args, **kwargs):
        if not self.pk and TTSConfiguration.objects.exists():
            raise ValidationError("There can be only one TTSConfiguration instance")
        super().save(*args, **kwargs)
        from tts.infer_gradio_api import set_custom_model
        set_custom_model(self.checkpoint, self.vocab, self.config)
