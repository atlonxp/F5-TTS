import os

from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin

from .models.config.models import TTSConfiguration
from .models.speaker.models import Speaker, ReferenceAudio
from .models.tts.models import UsageLog


class CustomSelectWidget(forms.Select):
    class Media:
        css = {
            'all': ('css/tailwind.css',)  # Adjust the path to where your CSS file is located in your static files.
        }


# --------------------------------------
# TTSConfiguration
# --------------------------------------


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


# --------------------------------------
# Speaker
# --------------------------------------

@admin.register(ReferenceAudio)
class ReferenceAudioAdmin(ModelAdmin):
    list_display = ['uuid', 'text', 'audio_player', 'formatted_duration']
    list_display_links = ['uuid']
    list_filter = ['text']
    search_fields = ['text']

    def ref_audio(self, obj):
        if obj.audio:
            link = obj.audio.url
            return mark_safe(f'<a href="{link}" target="_blank">{obj.audio.original_filename}</a>')
        return "No Audio"

    ref_audio.short_description = 'Audio'

    def audio_player(self, obj):
        """Embed an HTML5 audio player for the generated audio."""
        if obj.audio:
            return format_html(
                '<audio controls><source src="{}" type="audio/wav">Unsupport</audio>',
                obj.audio.url
            )
        return "❌"

    audio_player.short_description = "Audio"

    def formatted_duration(self, obj):
        return "{:.2f}".format(obj.duration)

    formatted_duration.short_description = 'Duration'


@admin.register(Speaker)
class SpeakerAdmin(ModelAdmin):
    list_display = ['speaker_id', 'gender', 'name', 'ref_text', 'ref_audio', 'formatted_duration', 'default']
    list_filter = ['gender']
    list_display_links = ['name']
    list_editable = ['default']
    ordering = ('gender', 'name')

    def ref_text(self, obj):
        return obj.reference.text[:50]

    ref_text.short_description = 'Ref. Text'

    def ref_audio(self, obj):
        if obj.reference and obj.reference.audio:
            link = obj.reference.audio.url
            return mark_safe(f'<a href="{link}" target="_blank">{obj.reference.audio.original_filename}</a>')
        return "No Audio"

    ref_audio.short_description = 'Ref. Audio'

    def formatted_duration(self, obj):
        if obj.reference:
            return "{:.2f}".format(obj.reference.duration)

    formatted_duration.short_description = 'Duration'


# --------------------------------------
# UsageLog
# --------------------------------------

def get_speaker_choices():
    choices = [("", "---------")]  # Add an empty choice for optional selection
    for speaker in Speaker.objects.all():
        choices.append((speaker.pk, f"{speaker.name} ({speaker.gender} - {speaker.language})"))
    return choices

def get_reference_choices():
    choices = [("", "---------")]
    for reference in ReferenceAudio.objects.all():
        choices.append((reference.pk, reference.text))
    return choices

class UsageLogForm(forms.ModelForm):
    generated_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': "mt-2 border border-base-200 bg-white font-medium placeholder-base-400 rounded shadow-sm text-font-default-light text-sm focus:ring focus:ring-primary-300 focus:border-primary-600 focus:outline-none group-[.errors]:border-red-600 group-[.errors]:focus:ring-red-200 dark:bg-base-900 dark:border-base-700 dark:text-font-default-dark dark:focus:border-primary-600 dark:focus:ring-primary-700 dark:focus:ring-opacity-50 dark:group-[.errors]:border-red-500 dark:group-[.errors]:focus:ring-red-600/40 px-3 py-2 w-full pr-8 max-w-2xl appearance-none"
        })
    )
    speaker = forms.ChoiceField(
        choices=[], required=False,
        widget=CustomSelectWidget(attrs={
            'class': "border border-base-200 bg-white font-medium min-w-20 placeholder-base-400 rounded shadow-sm text-font-default-light text-sm focus:ring focus:ring-primary-300 focus:border-primary-600 focus:outline-none group-[.errors]:border-red-600 group-[.errors]:focus:ring-red-200 dark:bg-base-900 dark:border-base-700 dark:text-font-default-dark dark:focus:border-primary-600 dark:focus:ring-primary-700 dark:focus:ring-opacity-50 dark:group-[.errors]:border-red-500 dark:group-[.errors]:focus:ring-red-600/40 px-3 py-2 w-full pr-8 max-w-2xl appearance-none"
        })
    )
    custom_reference = forms.ChoiceField(
        choices=[], required=False,
        widget=CustomSelectWidget(attrs={
            'class': "border border-base-200 bg-white font-medium min-w-20 placeholder-base-400 rounded shadow-sm text-font-default-light text-sm focus:ring focus:ring-primary-300 focus:border-primary-600 focus:outline-none group-[.errors]:border-red-600 group-[.errors]:focus:ring-red-200 dark:bg-base-900 dark:border-base-700 dark:text-font-default-dark dark:focus:border-primary-600 dark:focus:ring-primary-700 dark:focus:ring-opacity-50 dark:group-[.errors]:border-red-500 dark:group-[.errors]:focus:ring-red-600/40 px-3 py-2 w-full pr-8 max-w-2xl appearance-none"
        })
    )

    class Meta:
        model = UsageLog
        fields = ['generated_text', 'speaker', 'custom_reference']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['speaker'].choices = get_speaker_choices()
            self.fields['custom_reference'].choices = get_reference_choices()

    def clean_speaker(self):
        """ Convert the speaker ID (string) into a Speaker instance """
        speaker_id = self.cleaned_data.get('speaker')
        if speaker_id:
            return Speaker.objects.get(pk=speaker_id)
        return None

    def clean_custom_reference(self):
        """ Convert the reference ID (string) into a ReferenceAudio instance """
        reference_id = self.cleaned_data.get('custom_reference')
        if reference_id:
            return ReferenceAudio.objects.get(pk=reference_id)
        return None

    def clean(self):
        """ Ensure at least one of `speaker` or `custom_reference` is selected """
        cleaned_data = super().clean()
        speaker = cleaned_data.get('speaker')
        custom_reference = cleaned_data.get('custom_reference')
        if not speaker and not custom_reference:
            raise ValidationError("You must select at least one: Speaker or Reference Audio.")
        return cleaned_data
        
    def save(self, commit=True):
        instance = super().save(commit=False)

        # The cleaned_data fields will already contain proper instances
        instance.speaker = self.cleaned_data['speaker']
        instance.custom_reference = self.cleaned_data['custom_reference']

        if commit:
            instance.save()
        return instance
        

@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    form = UsageLogForm

    list_display = [
        'id', 'generated_text', 'speaker', 'custom_reference', 'formatted_timestamp',
        # 'audio_player',
        'enhanced_audio_player',
    ]
    list_display_links = ['id', 'generated_text']
    list_filter = ['speaker', 'custom_reference']
    # search_fields = ['generated_text']
    readonly_fields = ['speaker', 'custom_reference', 'generated_text', 'audio_player', 'enhanced_audio_player',
                       'spectrogram_viewer', 'timestamp', ]

    def get_readonly_fields(self, request, obj=None):
        """
        - If `obj` is `None` (creating new instance), `speaker` and `custom_reference` are editable.
        - If `obj` exists (editing existing instance), `speaker` and `custom_reference` are readonly.
        """
        readonly_fields = ['audio_player', 'enhanced_audio_player', 'spectrogram_viewer', 'timestamp']
        if obj:
            readonly_fields += ['speaker', 'custom_reference', 'generated_text', ]
        return readonly_fields

    def formatted_timestamp(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    formatted_timestamp.short_description = 'Created'

    # link mode
    # def view_generated_audio(self, obj):
    #     """Generate a clickable link to play the generated audio."""
    #     if obj.generated_audio:
    #         return format_html('<a href="{}" target="_blank">🔊</a>', obj.generated_audio.url)
    #     return "❌"
    # view_generated_audio.short_description = "Audio"
    #
    # def view_enhanced_audio(self, obj):
    #     """Generate a clickable link to play the enhanced audio."""
    #     if obj.enhanced_audio:
    #         return format_html('<a href="{}" target="_blank">🔊</a>', obj.enhanced_audio.url)
    #     return "❌"
    # view_enhanced_audio.short_description = "ENH Audio"

    # audio player mode
    def audio_player(self, obj):
        """Embed an HTML5 audio player for the generated audio."""
        if obj.generated_audio:
            return format_html(
                '<audio controls><source src="{}" type="audio/wav">Your browser does not support the audio element.</audio>',
                obj.generated_audio.url
            )
        return "❌"

    audio_player.short_description = "Audio"

    def enhanced_audio_player(self, obj):
        """Embed an HTML5 audio player for the enhanced audio."""
        if obj.enhanced_audio:
            return format_html(
                '<audio controls><source src="{}" type="audio/wav">Your browser does not support the audio element.</audio>',
                obj.enhanced_audio.url
            )
        return "❌"

    enhanced_audio_player.short_description = "ENH Audio"

    def view_spectrogram(self, obj):
        """Generate a clickable link to view the spectrogram image."""
        if obj.spectrogram:
            return format_html('<a href="{}" target="_blank">📈</a>', obj.spectrogram.url)
        return "❌"

    view_spectrogram.short_description = "Spectrogram"

    # Spectrogram viewer in detail view
    def spectrogram_viewer(self, obj):
        """Display a clickable image preview of the spectrogram."""
        if obj.spectrogram:
            return format_html(
                '<a href="{0}" target="_blank">'
                '<img src="{0}" style="max-height:200px; max-width:100%;" />'
                '</a>',
                obj.spectrogram.url
            )
        return "❌"

    spectrogram_viewer.short_description = "Spectrogram Preview"
