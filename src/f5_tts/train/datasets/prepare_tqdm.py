import ujson as json
from pathlib import Path
from importlib.resources import files

from p_tqdm import p_imap
from datasets.arrow_writer import ArrowWriter
from f5_tts.model.utils import convert_char_to_pinyin, repetition_found

# ————————————————————————————
# Configuration
# ————————————————————————————
MAX_WORKERS  = 128
TOKENIZER    = "pinyin"      # or "char"
POLYPHONE    = True
LANGS        = ["TH", "EN", "ZH"]

BASE         = Path("/project/lt200249-speech/hall/datasets/multi-tts")
SAVE_BASE    = Path(files("f5_tts").joinpath("../../")) / "data"
DATASET_NAME = f"Custom_{'_'.join(LANGS)}_{TOKENIZER}"
SAVE_DIR     = SAVE_BASE / DATASET_NAME
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# your opt-out sets
OUT_ZH = {
    "ZH_B00041_S06226", "ZH_B00042_S09204", "ZH_B00065_S09430",
    "ZH_B00065_S09431", "ZH_B00066_S09327", "ZH_B00066_S09328",
}
ZH_FILTERS = {"い", "て"}

OUT_EN = {
    "EN_B00013_S00913", "EN_B00042_S00120", "EN_B00055_S04111", "EN_B00061_S00693",
    "EN_B00061_S01494", "EN_B00061_S03375", "EN_B00059_S00092", "EN_B00111_S04300",
    "EN_B00087_S03811", "EN_B00059_S00950", "EN_B00089_S00946",
    "EN_B00078_S05127", "EN_B00070_S04089", "EN_B00074_S09659", "EN_B00061_S06983",
    "EN_B00061_S07060", "EN_B00059_S08397", "EN_B00082_S06192", "EN_B00091_S01238",
    "EN_B00089_S07349", "EN_B00070_S04343", "EN_B00061_S02400", "EN_B00076_S01262",
    "EN_B00068_S06467", "EN_B00076_S02943", "EN_B00064_S05954", "EN_B00061_S05386",
    "EN_B00066_S06544", "EN_B00076_S06944", "EN_B00072_S08620", "EN_B00076_S07135",
    "EN_B00076_S09127", "EN_B00065_S00497", "EN_B00059_S06227", "EN_B00063_S02859",
    "EN_B00075_S01547", "EN_B00061_S08286", "EN_B00079_S02901", "EN_B00092_S03643",
    "EN_B00096_S08653", "EN_B00063_S04297", "EN_B00063_S04614", "EN_B00079_S04698",
    "EN_B00104_S01666", "EN_B00061_S09504", "EN_B00061_S09694", "EN_B00065_S05444",
    "EN_B00063_S06860", "EN_B00065_S05725", "EN_B00069_S07628", "EN_B00083_S03875",
    "EN_B00071_S07665", "EN_B00071_S07665", "EN_B00062_S04187", "EN_B00065_S09873",
    "EN_B00065_S09922", "EN_B00084_S02463", "EN_B00067_S05066", "EN_B00106_S08060",
    "EN_B00073_S06399", "EN_B00073_S09236", "EN_B00087_S00432", "EN_B00085_S05618",
    "EN_B00064_S01262", "EN_B00072_S01739", "EN_B00059_S03913", "EN_B00069_S04036",
    "EN_B00067_S05623", "EN_B00060_S05389", "EN_B00060_S07290", "EN_B00062_S08995",
}
EN_FILTERS = {"ا", "い", "て"}

TRANSLATOR = str.maketrans({",": "，", "!": "！", "?": "？"})


def process_json_file(task):
    """
    task = (lang_tag, path_to_one_json_file)
    That .json is assumed to contain exactly one JSON object:
      { "id": "...", "wav": "...", "text": "...", "duration": ..., "phone": "..." }
    """
    lang, json_path = task

    bad_zh = bad_en = bad_th = 0
    samples, durations, vocab = [], [], set()
    errors = []

    try:
        obj = json.load(json_path.open("r", encoding="utf-8"))
        text = obj["text"]
        wavid = obj["wav"].split("/", 1)[1]

        # —— OPT-OUT FILTERS ——
        if lang == "ZH":
            if (
                wavid in OUT_ZH
                or any(ch in text for ch in ZH_FILTERS)
                or repetition_found(text)
            ):
                bad_zh += 1
                return samples, durations, vocab, bad_zh, bad_en, bad_th, errors
            text = text.translate(TRANSLATOR)

        elif lang == "EN":
            if (
                wavid in OUT_EN
                or any(ch in text for ch in EN_FILTERS)
                or repetition_found(text, length=4)
            ):
                bad_en += 1
                return samples, durations, vocab, bad_zh, bad_en, bad_th, errors

        # —— NORMALIZE & TOKENIZE ——
        dur = obj["duration"]
        if lang == "TH" and not text.startswith(" "):
            text = " " + text

        if TOKENIZER == "pinyin":
            text = convert_char_to_pinyin([text], polyphone=POLYPHONE)[0]

        # —— MAIN SAMPLE ——
        audio_file = json_path.with_suffix(".wav")
        samples.append({
            "audio_path": str(audio_file),
            "text":       text,
            "duration":   dur
        })
        durations.append(dur)
        vocab.update(text)

        # —— TH: also emit the “phone” transcript ——
        if lang == "TH":
            phone = obj.get("phone", "")
            if not phone.startswith(" "):
                phone = " " + phone
            if TOKENIZER == "pinyin":
                phone = convert_char_to_pinyin([phone], polyphone=POLYPHONE)[0]
            samples.append({
                "audio_path": str(audio_file),
                "text":       phone,
                "duration":   dur
            })
            durations.append(dur)
            vocab.update(phone)

    except Exception:
        errors.append(str(json_path))

    return samples, durations, vocab, bad_zh, bad_en, bad_th, errors


def main():
    # 1) build the list of (lang, json_file) tasks
    tasks = []
    for lang in LANGS:
        folder = {
            "ZH": BASE / "zh",
            "EN": BASE / "en" / "emilia" / "wavs",
            "TH": BASE / "th" / "gigaspeech2" / "wavs",
        }[lang]
        for j in folder.glob("*.json"):
            tasks.append((lang, j))

    # 2) process in parallel, streaming results with p_imap
    results = p_imap(
        process_json_file,
        tasks,
        num_cpus=MAX_WORKERS,
        desc="Shard→samples"
    )

    # 3) open an ArrowWriter and fold in all samples
    writer        = ArrowWriter(path=str(SAVE_DIR / "raw.arrow"))
    all_durations = []
    all_vocab     = set()
    tot_bad_zh = tot_bad_en = tot_bad_th = 0
    tot_errors = []

    for samples, durs, vocab, bzh, ben, bth, errors in results:
        for s in samples:
            writer.write(s)
        all_durations.extend(durs)
        all_vocab.update(vocab)
        tot_bad_zh += bzh
        tot_bad_en += ben
        tot_bad_th += bth
        tot_errors += errors

    writer.close()

    # 4) ancillary files
    (SAVE_DIR / "duration.json").write_text(
        json.dumps({"duration": all_durations}, ensure_ascii=False),
        encoding="utf-8"
    )
    (SAVE_DIR / "vocab.txt").write_text(
        "\n".join(sorted(all_vocab)), encoding="utf-8"
    )

    # 5) summary
    hours = sum(all_durations) / 3600
    print(f"\n=== {DATASET_NAME} summary ===")
    print(f"vocab size: {len(all_vocab)}")
    print(f"total hours: {hours:.2f}")
    print(f"bad ZH: {tot_bad_zh}, bad EN: {tot_bad_en}, bad TH: {tot_bad_th}")
    print(f"Error JSON: {len(tot_errors)}")
    for err in tot_errors:
        print(f"  : {err}")


if __name__ == "__main__":
    main()
