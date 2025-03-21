import json
import logging
import os
import tempfile
from importlib.resources import files

import click
import gradio as gr
import soundfile as sf
import torchaudio

from f5_tts.infer.infer_gradio import load_f5tts, load_custom
from f5_tts.infer.utils_infer_basic import get_available_models, get_vocab_files, get_model_configs

logger = logging.getLogger(__name__)

# -------------------------------------
# VoiceFixer
# -------------------------------------
from voicefixer import VoiceFixer

voicefixer = VoiceFixer()

# -------------------------------------
# F5-TTS
# -------------------------------------
from f5_tts.infer.utils_infer import (
    load_vocoder,
    preprocess_ref_audio_text,
    infer_process,
    remove_silence_for_generated_wav,
    save_spectrogram, device
)

DEFAULT_TTS_MODEL = "F5-TTS"
tts_model_choice = DEFAULT_TTS_MODEL

DEFAULT_TTS_MODEL_CFG = [
    "hf://SWivid/F5-TTS/F5TTS_v1_Base/model_1250000.safetensors",
    "hf://SWivid/F5-TTS/F5TTS_v1_Base/vocab.txt",
    json.dumps(dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)),
]

cwd = os.path.abspath(__file__).split('/')
project_root = '/'.join(cwd[:-4])
CKPTS_DIR = os.path.join(project_root, "ckpts")
DATA_DIR = os.path.join(project_root, "data")
DEMO_DIR = os.path.join(project_root, "demo")

vocoder = load_vocoder()

F5TTS_ema_model = load_f5tts()
custom_ema_model, pre_custom_path = None, ""

chat_model_state = None
chat_tokenizer_state = None


def update_dropdowns():
    """Fetch latest models, vocab, and config dynamically"""
    return (
        gr.Dropdown.update(choices=get_available_models()),
        gr.Dropdown.update(choices=get_vocab_files()),
        gr.Dropdown.update(choices=get_model_configs())
    )


def get_speakers():
    speakers = sorted(
        [f.replace(".wav", "").replace("_", " ") for f in os.listdir(DEMO_DIR) if f.endswith(".wav")]
    )
    return ["Select Speaker"] + speakers


def infer(
        ref_audio_orig,
        ref_text,
        gen_text,
        model,
        remove_silence,
        cross_fade_duration=0.15,
        nfe_step=32,
        speed=1,
        show_info=gr.Info,
):
    if not ref_audio_orig:
        gr.Warning("Please provide reference audio.")
        return gr.update(), gr.update(), ref_text

    if not gen_text.strip():
        gr.Warning("Please enter text to generate.")
        return gr.update(), gr.update(), ref_text

    ref_audio, ref_text = preprocess_ref_audio_text(ref_audio_orig, ref_text, show_info=show_info)

    if "F5-TTS" in model:
        ema_model = F5TTS_ema_model
    elif isinstance(model, list) and model[0] == "Custom":
        global custom_ema_model, pre_custom_path
        if pre_custom_path != model[1]:
            show_info("Loading Custom TTS model...")
            custom_ema_model = load_custom(model[1], vocab_path=model[2], model_cfg=model[3])
            pre_custom_path = model[1]
        ema_model = custom_ema_model

    final_wave, final_sample_rate, combined_spectrogram = infer_process(
        ref_audio,
        ref_text,
        gen_text,
        ema_model,
        vocoder,
        cross_fade_duration=cross_fade_duration,
        nfe_step=nfe_step,
        speed=speed,
        show_info=show_info,
        progress=gr.Progress(),
    )

    # Remove silence
    if remove_silence:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            sf.write(f.name, final_wave, final_sample_rate)
            remove_silence_for_generated_wav(f.name)
            final_wave, _ = torchaudio.load(f.name)
        final_wave = final_wave.squeeze().cpu().numpy()

    # Save the spectrogram
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_spectrogram:
        spectrogram_path = tmp_spectrogram.name
        save_spectrogram(combined_spectrogram, spectrogram_path)

    # enhance audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        sf.write(f.name, final_wave, final_sample_rate)
        voicefixer.restore(
            input=f.name, output=f.name,
            cuda=True if device == "cuda" else False,
            mode=0
        )
        enhanced_wave, enhanced_sample_rate = torchaudio.load(f.name)
        # mel-spec from enhanced audio -- disabled as it cause slow processing
        # with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_spectrogram:
        #     enhanced_spectrogram_path = generate_spectrogram(f.name, tmp_spectrogram.name)
    enhanced_wave = enhanced_wave.squeeze().cpu().numpy()

    return (final_sample_rate, final_wave), spectrogram_path, ref_text, (enhanced_sample_rate, enhanced_wave)


def update_demo_choices():
    return gr.update(choices=get_speakers(), value="Select Speaker")


# Function to load selected demo
def load_speaker(selected_demo):
    """Fetches the selected audio file and its associated transcript."""
    if selected_demo == "Select Speaker":
        return gr.update(value=None), gr.update(value="")

    # Convert the selected name back to the filename format
    filename = selected_demo.replace(" ", "_") + ".wav"
    audio_path = os.path.join(DEMO_DIR, filename)

    if not os.path.exists(audio_path):
        return gr.update(value=None), gr.update(value="")

    transcript_path = audio_path.replace(".wav", ".txt")  # Assuming text file follows the same naming
    text_content = open(transcript_path, "r", encoding="utf-8").read() if os.path.exists(transcript_path) else ""

    return gr.update(value=audio_path), gr.update(value=text_content)


with gr.Blocks() as app_tts:
    gr.Markdown("# Basic TTS")
    with gr.Row():
        demo_selector = gr.Dropdown(
            choices=get_speakers(),
            label="Select a speaker reference audio and transcript",
            value="Select Speaker"
        )
        refresh_button = gr.Button("Refresh List")
        refresh_button.click(update_demo_choices, outputs=demo_selector)

    with gr.Row():
        ref_audio_input = gr.Audio(label="Reference Audio", type="filepath")
        ref_text_input = gr.Textbox(
            label="Reference Text",
            info="Leave blank to automatically transcribe the reference audio. If you enter text it will override automatic transcription.",
            lines=7,
        )
    gen_text_input = gr.Textbox(label="Text to Generate", lines=5)
    generate_btn = gr.Button("Synthesize", variant="primary")
    with gr.Accordion("Advanced Settings", open=False):
        remove_silence = gr.Checkbox(
            label="Remove Silences",
            info="The model tends to produce silences, especially on longer audio. We can manually remove silences if needed. Note that this is an experimental feature and may produce strange results. This will also increase generation time.",
            value=False,
        )
        speed_slider = gr.Slider(
            label="Speed", info="Adjust the speed of the audio.",
            minimum=0.3, maximum=2.0, value=1.0, step=0.1,
        )
        nfe_slider = gr.Slider(
            label="NFE Steps", info="Set the number of denoising steps.",
            minimum=4, maximum=64, value=32, step=2,
        )
        cross_fade_duration_slider = gr.Slider(
            label="Cross-Fade Duration (s)", info="Set the duration of the cross-fade between audio clips.",
            minimum=0.0, maximum=1.0, value=0.15, step=0.01,
        )

    spectrogram_output = gr.Image(label="Spectrogram")
    with gr.Row():
        audio_output = gr.Audio(label="Synthesized Audio")
        audio_enhanced = gr.Audio(label="Enchanced Audio")

    demo_selector.change(load_speaker, inputs=[demo_selector], outputs=[ref_audio_input, ref_text_input])


    def basic_tts(
            ref_audio_input, ref_text_input, gen_text_input,
            remove_silence, cross_fade_duration_slider, nfe_slider, speed_slider,
    ):
        audio_out, spectrogram_path, ref_text_out, audio_enhanced_out = infer(
            ref_audio_input, ref_text_input, gen_text_input,
            tts_model_choice,
            remove_silence,
            cross_fade_duration=cross_fade_duration_slider, nfe_step=nfe_slider, speed=speed_slider,
        )

        return audio_out, spectrogram_path, ref_text_out, audio_enhanced_out


    generate_btn.click(
        basic_tts,
        inputs=[
            ref_audio_input, ref_text_input, gen_text_input,
            remove_silence, cross_fade_duration_slider, nfe_slider, speed_slider,
        ],
        outputs=[audio_output, spectrogram_output, ref_text_input, audio_enhanced],
    )

with gr.Blocks() as app:
    gr.Markdown("""
        # F5 TTS for Thai by Watthanasak Jeamwatthanachai, PhD

        This is a local web UI for F5-TTS with advanced batch processing support. This app supports the following TTS models:

        * [F5-TTS](https://arxiv.org/abs/2410.06885) (A Fairytaler that Fakes Fluent and Faithful Speech with Flow Matching)

        The checkpoints currently support English, Chinese, and Thai (experiments).

        **NOTE: Reference text will be automatically transcribed with Whisper if not provided**

        * English and Chinese only.
        * Thai requires a reference text. Whisper is not yet supported for Thai but will be added soon.
        * For best results, keep your reference clips short (<15s). Ensure the audio is fully uploaded before generating.
        """)

    last_used_custom = files("f5_tts").joinpath("infer/.cache/last_used_custom_model_info.txt")


    def load_last_used_custom():
        try:
            custom = []
            with open(last_used_custom, "r", encoding="utf-8") as f:
                for line in f:
                    custom.append(line.strip())
            return custom
        except FileNotFoundError:
            last_used_custom.parent.mkdir(parents=True, exist_ok=True)
            return DEFAULT_TTS_MODEL_CFG


    def switch_tts_model(new_choice):
        global tts_model_choice
        if new_choice == "Custom":  # override in case webpage is refreshed
            custom_ckpt_path, custom_vocab_path, custom_model_cfg = load_last_used_custom()
            tts_model_choice = ["Custom", custom_ckpt_path, custom_vocab_path, json.loads(custom_model_cfg)]
            return (
                gr.update(visible=True, value=custom_ckpt_path),
                gr.update(visible=True, value=custom_vocab_path),
                gr.update(visible=True, value=custom_model_cfg),
            )
        else:
            tts_model_choice = new_choice
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)


    def set_custom_model(custom_ckpt_path, custom_vocab_path, custom_model_cfg):
        global tts_model_choice
        tts_model_choice = ["Custom", custom_ckpt_path, custom_vocab_path, json.loads(custom_model_cfg)]
        with open(last_used_custom, "w", encoding="utf-8") as f:
            f.write(custom_ckpt_path + "\n" + custom_vocab_path + "\n" + custom_model_cfg + "\n")


    with gr.Row():
        choose_tts_model = gr.Radio(
            choices=[DEFAULT_TTS_MODEL, "Custom"], label="Choose TTS Model", value=DEFAULT_TTS_MODEL
        )
        custom_ckpt_path = gr.Dropdown(
            choices=get_available_models(),
            value=load_last_used_custom()[0],
            allow_custom_value=True,
            label="Model: local_path | hf://user_id/repo_id/model_ckpt",
            visible=False,
        )
        custom_vocab_path = gr.Dropdown(
            choices=get_vocab_files(),
            value=load_last_used_custom()[1],
            allow_custom_value=True,
            label="Vocab: local_path | hf://user_id/repo_id/vocab_file",
            visible=False,
        )
        custom_model_cfg = gr.Dropdown(
            choices=get_model_configs(),
            value=load_last_used_custom()[2],
            allow_custom_value=True,
            label="Config: in a dictionary form",
            visible=False,
        )

    choose_tts_model.change(
        switch_tts_model,
        inputs=[choose_tts_model],
        outputs=[custom_ckpt_path, custom_vocab_path, custom_model_cfg],
        show_progress="hidden",
    )
    custom_ckpt_path.change(
        set_custom_model,
        inputs=[custom_ckpt_path, custom_vocab_path, custom_model_cfg],
        show_progress="hidden",
    )
    custom_vocab_path.change(
        set_custom_model,
        inputs=[custom_ckpt_path, custom_vocab_path, custom_model_cfg],
        show_progress="hidden",
    )
    custom_model_cfg.change(
        set_custom_model,
        inputs=[custom_ckpt_path, custom_vocab_path, custom_model_cfg],
        show_progress="hidden",
    )

    gr.TabbedInterface(
        [app_tts],
        ["Basic-TTS"],
    )


@click.command()
@click.option("--port", "-p", default=55556, type=int, help="Port to run the app on")
@click.option("--host", "-H", default="0.0.0.0", help="Host to run the app on")
@click.option("--share", "-s", default=False, is_flag=True, help="Share the app via Gradio share link", )
@click.option("--api", "-a", default=True, is_flag=True, help="Allow API access")
@click.option("--root_path", "-r", default="/f5/playground", type=str,
              help='The root path (or "mount point") of the application, if it\'s not served from the root ("/") of the domain. Often used when the application is behind a reverse proxy that forwards requests to the application, e.g. set "/myapp" or full URL for application served at "https://example.com/myapp".', )
@click.option("--inbrowser", "-i", is_flag=True, default=False,
              help="Automatically launch the interface in the default web browser", )
def main(port, host, share, api, root_path, inbrowser):
    global app

    print(f"""
    Starting F5-TTS app with Gradio
    \t> host: {host}:{port}
    \t> allow_api: {api}
    \t> root_path: {root_path}
    """)

    app.queue(api_open=api).launch(
        server_name=host,
        server_port=port,
        share=share,
        show_api=api,
        root_path=root_path,
        inbrowser=inbrowser,
        allowed_paths=[
            "./demo",
        ]
    )


if __name__ == "__main__":
    main(args=["--port", "55556", "--host", "0.0.0.0", "--root_path", "/f5/playground"], standalone_mode=False)
