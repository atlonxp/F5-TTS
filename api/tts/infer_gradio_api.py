from gradio_client import Client, handle_file

client = Client("http://0.0.0.0:55556")


def switch_tts_model(new_choice: str = "Custom", verbose=False):
    if new_choice not in ['F5-TTS', 'E2-TTS', 'Custom']:
        raise ValueError(f"new_choice should be one of ['F5-TTS', 'E2-TTS', 'Custom'], but got {new_choice}")
    result = client.predict(
        new_choice,
        api_name="/switch_tts_model"
    )
    if verbose:
        print(result)
    return result


def set_custom_model(custom_ckpt_path: str, custom_vocab_path: str, custom_model_cfg: str, verbose=False):
    result = client.predict(
        custom_ckpt_path=custom_ckpt_path,
        custom_vocab_path=custom_vocab_path,
        custom_model_cfg=custom_model_cfg,
        api_name="/set_custom_model"
    )
    if verbose:
        print(result)
    return result


def load_speaker(speaker_name: str = "Select Speaker", verbose=False):
    result = client.predict(
        selected_demo="Select Speaker",
        api_name="/load_speaker"
    )
    print(result)

    if verbose:
        print(result)
    return result


def basic_tts(
        ref_audio_input, ref_text_input, gen_text_input,
        remove_silence=False,
        cross_fade_duration_slider=0.15,
        nfe_slider=32,
        speed_slider=1,
        verbose=False
):
    result = client.predict(
        ref_audio_input=handle_file(ref_audio_input),
        ref_text_input=ref_text_input,
        gen_text_input=gen_text_input,
        remove_silence=remove_silence,
        cross_fade_duration_slider=cross_fade_duration_slider,
        nfe_slider=nfe_slider,
        speed_slider=speed_slider,
        api_name="/basic_tts"
    )
    if verbose:
        print(result)
    return result


if __name__ == "__main__":
    ckpt, vocab, config = switch_tts_model(new_choice="Custom")
    set_custom_model(
        custom_ckpt_path=ckpt['value'],
        custom_vocab_path=vocab['value'],
        custom_model_cfg=config['value'],
        verbose=False
    )
    load_speaker()
