import os

from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin

from .models.config.models import TTSConfiguration
from .models.speaker.models import Speaker
from .models.tts.models import UsageLog


class CustomSelectWidget(forms.Select):
    class Media:
        css = {
            'all': ('css/tailwind.css',)  # Adjust the path to where your CSS file is located in your static files.
        }


def get_checkpoint_choices():
    checkpoint_dir = os.path.abspath(os.path.join(settings.BASE_DIR, "..", 'ckpts'))
    choices = [
        ("hf://SWivid/F5-TTS/F5TTS_Base/model_1200000.safetensors", "F5-TTS Base"),
    ]

    if os.path.isdir(checkpoint_dir):
        for root, dirs, files in os.walk(checkpoint_dir):
            for file in files:
                if file.endswith('.pt'):
                    full_path = os.path.join(root, file)
                    choices.append((full_path, full_path))
    return choices


def get_vocab_choices():
    checkpoint_dir = os.path.abspath(os.path.join(settings.BASE_DIR, "..", 'data'))
    choices = [
        ("hf://SWivid/F5-TTS/F5TTS_Base/vocab.txt", "F5-TTS Base"),
    ]

    if os.path.isdir(checkpoint_dir):
        for root, dirs, files in os.walk(checkpoint_dir):
            for file in files:
                if file == 'vocab.txt':
                    full_path = os.path.join(root, file)
                    choices.append((full_path, full_path))
    return choices


class TTSCheckpointForm(forms.ModelForm):
    # Override the checkpoint field with a dropdown
    checkpoint = forms.ChoiceField(
        choices=[], required=True,
        widget=CustomSelectWidget(attrs={
            'class': "border border-base-200 bg-white font-medium min-w-20 placeholder-base-400 rounded shadow-sm text-font-default-light text-sm focus:ring focus:ring-primary-300 focus:border-primary-600 focus:outline-none group-[.errors]:border-red-600 group-[.errors]:focus:ring-red-200 dark:bg-base-900 dark:border-base-700 dark:text-font-default-dark dark:focus:border-primary-600 dark:focus:ring-primary-700 dark:focus:ring-opacity-50 dark:group-[.errors]:border-red-500 dark:group-[.errors]:focus:ring-red-600/40 px-3 py-2 w-full pr-8 max-w-2xl appearance-none"
        })
    )
    vocab = forms.ChoiceField(
        choices=[], required=True,
        widget=CustomSelectWidget(attrs={
            'class': "border border-base-200 bg-white font-medium min-w-20 placeholder-base-400 rounded shadow-sm text-font-default-light text-sm focus:ring focus:ring-primary-300 focus:border-primary-600 focus:outline-none group-[.errors]:border-red-600 group-[.errors]:focus:ring-red-200 dark:bg-base-900 dark:border-base-700 dark:text-font-default-dark dark:focus:border-primary-600 dark:focus:ring-primary-700 dark:focus:ring-opacity-50 dark:group-[.errors]:border-red-500 dark:group-[.errors]:focus:ring-red-600/40 px-3 py-2 w-full pr-8 max-w-2xl appearance-none"
        })
    )

    class Meta:
        model = TTSConfiguration
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['checkpoint'].choices = get_checkpoint_choices()
        self.fields['vocab'].choices = get_vocab_choices()


@admin.register(TTSConfiguration)
class TTSConfigurationAdmin(ModelAdmin):
    def has_add_permission(self, request):
        if TTSConfiguration.objects.exists():
            return False
        return True

    form = TTSCheckpointForm


@admin.register(Speaker)
class SpeakerAdmin(ModelAdmin):
    list_display = ['speaker_id', 'gender', 'name', 'reference_text', 'ref_audio_link', 'formatted_duration',
                    'default']
    list_filter = ['gender']
    list_display_links = ['name']
    list_editable = ['default']
    ordering = ('gender', 'name')

    def formatted_duration(self, obj):
        return "{:.2f}".format(obj.duration)

    formatted_duration.short_description = 'Duration'

    def ref_audio_link(self, obj):
        link = obj.reference_audio.url if obj.reference_audio else None
        if link:
            return mark_safe(f'<a href="{link}" target="_blank">{obj}</a>')

    ref_audio_link.short_description = 'Reference Audio'


@admin.register(UsageLog)
class UsageLogAdmin(ModelAdmin):
    pass
