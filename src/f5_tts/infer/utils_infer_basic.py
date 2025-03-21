import json
import os
from pathlib import Path

from f5_tts.infer.infer_gradio import DEFAULT_TTS_MODEL_CFG

DEFAULT_V0_TTS_MODEL_CFG = [
    "hf://SWivid/F5-TTS/F5TTS_Base/model_1200000.safetensors",
    "hf://SWivid/F5-TTS/F5TTS_Base/vocab.txt",
    json.dumps(dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, text_mask_padding=False, conv_layers=4,
                    pe_attn_head=1)),
]

cwd = os.path.abspath(__file__).split('/')
project_root = '/'.join(cwd[:-4])
CKPTS_DIR = os.path.join(project_root, "ckpts")
DATA_DIR = os.path.join(project_root, "data")
DEMO_DIR = os.path.join(project_root, "demo")


# -------------------------------------
# utility function from infer_gradio.py
# -------------------------------------


def get_available_models():
    """Efficiently list all model checkpoint files (.pt, .safetensors) from CKPTS_DIR."""
    return (sorted(str(f) for f in Path(CKPTS_DIR).rglob("*.pt")) +
            sorted(str(f) for f in Path(CKPTS_DIR).rglob("*.safetensors")) +
            [DEFAULT_TTS_MODEL_CFG[0], DEFAULT_V0_TTS_MODEL_CFG[0]])


def get_vocab_files():
    """Efficiently list all vocab files from DATA_DIR."""
    return sorted(str(f) for f in Path(DATA_DIR).rglob("vocab.txt")) + [
        DEFAULT_TTS_MODEL_CFG[1], DEFAULT_V0_TTS_MODEL_CFG[1]
    ]


def get_model_configs():
    """Dynamically generate model configurations"""
    config_options = [
        DEFAULT_TTS_MODEL_CFG[2],
        DEFAULT_V0_TTS_MODEL_CFG[2],
        json.dumps(dict(dim=768, depth=18, heads=12, ff_mult=2, text_dim=512, conv_layers=4)),
    ]
    return config_options
