import json
import os
import re
import sys
import wave
from multiprocessing import cpu_count
from p_tqdm import p_map
import requests

# ──────────────────────────── LOGGING WARNINGS ──────────────────────────── #
import logging
logging.disable(logging.CRITICAL)
logging.disable(logging.INFO)

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)

# ──────────────────────────── CONFIG ──────────────────────────── #

# URL of your running Phonemizer server endpoint
PHONEMIZER_SERVER_URL = "http://127.0.0.1:8000/g2p/"

# Paths
dataset_path = "/project/lt200249-speech/hall/datasets/multi-tts/th/gigaspeech2/"
meta_csv     = os.path.join(dataset_path, "metadata_text_normal.csv")
wavs_path     = os.path.join(dataset_path, "wavs")

# ──────────────────────────── HELPER FUNCTIONS ──────────────────────────── #

def get_duration(wav_path: str) -> float:
    """Return the duration (in seconds) of a WAV file."""
    with wave.open(wav_path, 'rb') as wf:
        frames = wf.getnframes()
        rate   = wf.getframerate()
        return frames / float(rate)


def g2p_via_api(text: str) -> str:
    """
    Send {"text": "<thai sentence>"} to the Phonemizer server
    and return the "phoneme" field. Raises on HTTP errors.
    """
    try:
        resp = requests.post(
            PHONEMIZER_SERVER_URL,
            json={"text": text},
            timeout=(2, None)  # connect timeout=2s, read timeout=5s
        )
        resp.raise_for_status()
        return resp.json()["phoneme"]
    except Exception as e:
        # In case of failure, print a warning and return an empty string
        sys.stderr.write(f"[ERROR] G2P API failed for text: {text[:30]}...: {e}\n")
        return ""


def process_line(line: str):
    """
    Parse "relative/path/to.wav|transcript". If the WAV exists:
      1) compute duration,
      2) call g2p_via_api(transcript),
      3) build metadata dict and return (filename, metadata).
    Otherwise return None.
    """
    parts = line.strip().split("|")
    if len(parts) != 2:
        return None

    rel_path, transcript = parts
    filename = os.path.basename(rel_path)
    wav_full_path = os.path.join(wavs_path, filename)
    json_path = os.path.join(wavs_path, filename.replace('.wav', '.json'))
    if os.path.exists(json_path):
        # in case, there is json file, check if it is complete.
        # try:
        #     with open(file_path, 'r', encoding='utf-8') as f:
        #         data = json.load(f)
        #     REQUIRED_KEYS = {"id", "wav", "duration", "text", "phone", "phone2", "language"}
        #     missing_keys = REQUIRED_KEYS - data.keys()
        #     if not missing_keys:
        #         return None
        # except json.JSONDecodeError:
        #     pass
        # except Exception as e:
        #     pass
        return None

    if not os.path.exists(wav_full_path):
        # print(f'Not found {wav_full_path}, Error')
        return None

    # 1) Duration
    try:
        duration = get_duration(wav_full_path)
    except wave.Error:
        return None

    # 2) Phoneme via HTTP API
    tokens_phoneme = g2p_via_api(transcript)

    metadata = {
        "id":       filename,
        "wav":      wav_full_path,
        "duration": duration,
        "text":     transcript,
        "phone":    tokens_phoneme,
        "phone2":   tokens_phoneme.replace("-", " "),
        "language": "th"
    }
    return filename, metadata


def process_all(line: str) -> str:
    """
    Called in each worker. Runs process_line(), writes JSON, and returns status.
    """
    result = process_line(line)
    if result is None:
        parts = line.strip().split("|")
        fname = os.path.basename(parts[0]) if parts else "unknown"
        return f"{fname} json is not saved; skipped"

    filename, metadata = result
    jsonpath = metadata['wav'].replace('.wav', '.json')
    try:
        with open(jsonpath, 'w', encoding='utf-8') as jf:
            json.dump(metadata, jf, ensure_ascii=False, indent=2)
            # print(f'Saving {jsonpath}')
    except Exception as e:
        return f"{filename} write_error: {e}"

    return f"{filename} json is saved"


# ──────────────────────────── MAIN ENTRY ──────────────────────────── #

if __name__ == "__main__":
    # 1) Read all non-empty lines from the metadata CSV
    with open(meta_csv, 'r', encoding='utf-8') as metafile:
        lines = [l for l in metafile.readlines() if l.strip()]

    total = len(lines)
    if total == 0:
        print("No entries in metadata. Exiting.")
        sys.exit(0)

    print(f"Total lines to process: {total}")
    print(f"Spawning {cpu_count()} CPU worker processes (via p_map).")

    # 2) Use p_map to parallelize across all CPU cores
    results = p_map(process_all, lines, num_cpus=cpu_count())

    # for res in results:
    #     print(res)