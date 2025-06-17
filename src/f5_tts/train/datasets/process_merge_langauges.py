# merge_datasets.py

import json
from pathlib import Path
import pyarrow as pa
from pyarrow import ipc

SAVE_BASE = Path("/project/lt200249-speech/hall/workspaces/f5-tts/data")
LANGS = [
    # "th", 
    # "en", 
    "zh"
]

# 1) merge Arrow *stream* files
tables = []
for lang in LANGS:
    shard_dir = SAVE_BASE / f"custom_{lang}_pinyin"
    path      = shard_dir / "raw.arrow"
    print("Reading:", path)
    with path.open("rb") as f:
        # use the streaming reader
        reader = ipc.open_stream(f)
        tables.append(reader.read_all())

# concatenate
combined = pa.concat_tables(tables)

# write back out as a *file*-format if you like, or stick with stream:
out_dir = SAVE_BASE / "custom2_th_en_zh_pinyin"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "raw.arrow"
# here we choose to write a file-format IPC, so that open_file will work next time:
with ipc.new_file(out_path, combined.schema) as writer:
    writer.write_table(combined)

# 2) merge vocab...
master_vocab = set()
for lang in LANGS:
    vocab_path = SAVE_BASE / f"custom_{lang}_pinyin" / "vocab.txt"
    with vocab_path.open(encoding="utf-8") as f:
        master_vocab |= {l.strip() for l in f}
with (out_dir / "vocab.txt").open("w", encoding="utf-8") as f:
    f.write("\n".join(sorted(master_vocab)))

# 3) merge summaries...
all_summaries = []
for lang in LANGS:
    summary_path = SAVE_BASE / f"custom_{lang}_pinyin" / "summary.json"
    all_summaries.append(json.load(summary_path.open(encoding="utf-8")))
with (out_dir / "combined_summary.json").open("w", encoding="utf-8") as f:
    json.dump(all_summaries, f, ensure_ascii=False, indent=2)

print("Merge complete. Final dataset at:", out_path)