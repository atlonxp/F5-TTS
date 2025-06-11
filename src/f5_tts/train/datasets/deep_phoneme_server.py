import os
import re
import wave
import logging
import warnings

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pythainlp.tokenize import word_tokenize, sent_tokenize
from third_party.deep_phonemizer.phonemizer import Phonemizer

# ──────────────────────────── Logging / Warnings ──────────────────────────── #
logging.getLogger("uvicorn.error").disabled = True

logging.disable(logging.CRITICAL)
logging.disable(logging.INFO)
warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=UserWarning)

# ──────────────────────────── CONFIGURATION ──────────────────────────── #

# Path to your DeepPhonemizer checkpoint (adjust as needed)
PHONEMIZER_MODEL_PATH = "/home/wjeamwat/F5-TTS/src/third_party/DeepPhonemizer/ckpts/best_model.pt"

# If you eventually want to add a duration endpoint, set WAVS_PATH. For now, we only do text→phoneme
# WAVS_PATH = "/project/lt200249-speech/hall/datasets/multi-tts/th/gigaspeech2/wavs"

# ──────────────────────────── FASTAPI SETUP ──────────────────────────── #

app = FastAPI(
    title="Thai Phoneme API",
    description="Expose DeepPhonemizer as a simple HTTP service (CPU)",
    version="1.0.0",
)

# Global Phonemizer instance (loaded once at startup)
phonemizer = None

if phonemizer is None:
    # Force CPU inference
    phonemizer = Phonemizer.from_checkpoint(PHONEMIZER_MODEL_PATH, device="cpu")
    # Put model into half-precision to reduce memory
    phonemizer.predictor.model = phonemizer.predictor.model.half()

class G2PRequest(BaseModel):
    text: str


class G2PResponse(BaseModel):
    phoneme: str


@app.post("/g2p/", response_model=G2PResponse)
def do_g2p(request: G2PRequest):
    """
    Convert Thai text into a token-separated phoneme string.

    Request JSON:
        {
          "text": "สวัสดีครับ"
        }

    Response JSON:
        {
          "phoneme": "...-..."
        }
    """
    global phonemizer
    if phonemizer is None:
        # In case startup didn’t run
        raise HTTPException(status_code=500, detail="Phonemizer not initialized")

    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text field")

    # 1. Sentence segmentation
    sentences = sent_tokenize(text, engine="crfcut")
    all_sent_ph = []

    for sentence in sentences:
        # 2. Word tokenization
        tokens = word_tokenize(re.sub(r"\s+", " ", sentence.strip()), engine="attacut")
        tokens_ph = []

        # 3. Run phonemizer on each token
        for t in tokens:
            if t.isspace() or not t:
                tokens_ph.append("")
            else:
                # DeepPhonemizer inference (CPU), returns e.g. "ph1 ph2 ph3"
                ph_str = phonemizer(t, "th")
                # Join sub-phonemes with "-" to produce a single token-sep string
                tokens_ph.append("-".join(ph_str.split(" ")))

        # 4. Reconstruct the sentence's phoneme string, append a period
        sent_ph = f"{' '.join(tokens_ph).replace('  ', ' ')}."
        all_sent_ph.append(sent_ph)

    full_ph_str = " ".join(all_sent_ph).strip()
    return G2PResponse(phoneme=full_ph_str)