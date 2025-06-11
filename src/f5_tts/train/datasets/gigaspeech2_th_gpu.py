import json
import os
import re
import sys
import wave
from multiprocessing import Pool, current_process
from tqdm import tqdm  # pip install tqdm

from pythainlp.tokenize import word_tokenize, sent_tokenize
from third_party.deep_phonemizer.phonemizer import Phonemizer

# ──────────────────────────── LOGGING ──────────────────────────── #
import logging
logging.disable(logging.CRITICAL)
logging.disable(logging.INFO)

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)

# ──────────────────────────── GLOBALS ──────────────────────────── #

# Path to your DeepPhonemizer checkpoint
phonemizer_model_path = "/home/wjeamwat/F5-TTS/src/third_party/DeepPhonemizer/ckpts/best_model.pt"

# We will spawn exactly NUM_GPUS worker processes.
NUM_GPUS = 4

# These will be set in init_worker()
phonemizer = None
assigned_gpu = None

# Dataset paths
dataset_path = "/project/lt200249-speech/hall/datasets/multi-tts/th/gigaspeech2/"
meta_path = os.path.join(dataset_path, "metadata_text_normal.csv")
wavs_path = os.path.join(dataset_path, "wavs")


# ──────────────────────────── HELPER FUNCTIONS ──────────────────────────── #

def init_worker():
    """
    This function runs once per worker at startup (inside the Pool).
    It:
      1) Reads this worker’s identity (1,2,…,NUM_GPUS) from current_process()._identity[0].
      2) Computes assigned_gpu = (identity‐1) % NUM_GPUS.
      3) Sets CUDA_VISIBLE_DEVICES so PyTorch sees only that A100.
      4) Loads the phonemizer model ONE TIME into half‐precision on that GPU.
    """
    global phonemizer, assigned_gpu

    # Get the worker index in [1..pool_size]
    identity = current_process()._identity[0]  # 1-based index within the Pool
    assigned_gpu = (identity - 1) % NUM_GPUS   # maps 1→0, 2→1, 3→2, 4→3

    # Pin this process to only see the assigned GPU
    os.environ["CUDA_VISIBLE_DEVICES"] = str(assigned_gpu)
    
    # Load DeepPhonemizer onto that GPU (FP16)
    phonemizer = Phonemizer.from_checkpoint(phonemizer_model_path)
    phonemizer.predictor.model = phonemizer.predictor.model.half()

    print(f"[Worker {identity}] PID={os.getpid()} assigned to GPU {assigned_gpu}")


def get_duration(wav_path: str) -> float:
    """Return the duration (in seconds) of a .wav file."""
    with wave.open(wav_path, "rb") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        return frames / float(rate)


def g2p(text: str, lang='th', token_sep='-', punctuation=".") -> str:
    """
    Convert Thai text to a phoneme string using the already‐loaded `phonemizer`.
    Because init_worker() has run, `phonemizer` is on the correct GPU.
    """
    # Break text into sentences
    sentences = sent_tokenize(text, engine="crfcut")
    all_sentences_ph = []

    for sentence in sentences:
        # Tokenize the sentence
        tokens = word_tokenize(re.sub(r"\s+", " ", sentence.strip()), engine="attacut")
        tokens_ph = []
        for t in tokens:
            if not t.isspace():
                # Each call invokes GPU inference on the assigned A100
                ph_str = phonemizer(t, lang)  # e.g. "ph1 ph2 ph3"
                tokens_ph.append(token_sep.join(ph_str.split(" ")))
            else:
                tokens_ph.append("")

        sent_ph = f"{' '.join(tokens_ph).replace('  ', ' ')}{punctuation}"
        all_sentences_ph.append(sent_ph)

    return " ".join(all_sentences_ph).strip()


def process_line(line: str):
    """
    Parse "relative/path/to.wav|transcript".
    If wav exists, compute duration + g2p() and return (filename, metadata_dict).
    Otherwise return None.
    """
    parts = line.strip().split("|")
    if len(parts) != 2:
        return None

    rel_path, transcript = parts
    filename = os.path.basename(rel_path)
    wav_full_path = os.path.join(wavs_path, filename)
    if not os.path.exists(wav_full_path):
        return None

    # 1) Duration
    try:
        duration = get_duration(wav_full_path)
    except wave.Error:
        return None

    # 2) Phonemes (GPU inference)
    tokens_phoneme = g2p(transcript, lang="th", token_sep="-", punctuation=".")

    meta = {
        "id": filename,
        "wav": wav_full_path,
        "duration": duration,
        "text": transcript,
        "phone": tokens_phoneme,
        "phone2": tokens_phoneme.replace("-", " "),
        "language": "th",
    }
    return filename, meta


def process_all(line: str) -> str:
    """
    Called in each worker. Runs process_line(), writes JSON, and returns a status.
    """
    result = process_line(line)
    if result is None:
        parts = line.strip().split("|")
        fname = os.path.basename(parts[0]) if parts else "unknown"
        return f"{fname} skipped"

    filename, metadata = result
    json_path = metadata["wav"].replace(".wav", ".json")
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(metadata, jf, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"{filename} write_error: {e}"

    return f"{filename} saved"


# ──────────────────────────── MAIN ──────────────────────────── #

if __name__ == "__main__":
    # 1) Read all non‐empty lines from metadata CSV
    with open(meta_path, "r", encoding="utf-8") as f:
        lines = [l for l in f.readlines() if l.strip()]

    total_lines = len(lines)
    if total_lines == 0:
        print("No entries found in metadata. Exiting.")
        sys.exit(0)

    print(f"Total lines to process: {total_lines}")
    print(f"Spawning {NUM_GPUS} worker processes (one per A100).")

    # 2) Create a Pool with NUM_GPUS workers, each calling init_worker()
    with Pool(processes=NUM_GPUS, initializer=init_worker) as pool:
        # We use imap_unordered so we can wrap with tqdm for a live progress bar.
        for status in tqdm(pool.imap_unordered(process_all, lines), total=total_lines):
            print(status)