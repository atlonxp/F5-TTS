# merge_datasets.py

import json
from pathlib import Path
import pyarrow as pa
from pyarrow import ipc

SAVE_BASE = Path("/project/lt200249-speech/hall/data")
LANGS = ["ZH","EN","TH"]

# 1) merge Arrow files
tables = []
for lang in LANGS:
    path = SAVE_BASE/f"Custom_{lang}_pinyin"/"raw.arrow"
    with ipc.open_file(path) as reader:
        tables.append(reader.read_all())

combined = pa.concat_tables(tables)
out_path = SAVE_BASE/"Custom_ZH_EN_TH_pinyin"/"raw.arrow"
out_path.parent.mkdir(parents=True, exist_ok=True)
with ipc.new_file(out_path, combined.schema) as writer:
    writer.write_table(combined)

# 2) merge vocab sets
master_vocab = set()
for lang in LANGS:
    lines = open(SAVE_BASE/f"Custom_{lang}_pinyin"/"vocab.txt",encoding="utf-8")
    master_vocab |= set(l.strip() for l in lines)
with open(out_path.parent/"vocab.txt","w",encoding="utf-8") as f:
    f.write("\n".join(sorted(master_vocab)))

# 3) (optional) combine summaries
all_summaries = []
for lang in LANGS:
    summary = json.load(open(
        SAVE_BASE/f"Custom_{lang}_pinyin"/"summary.json", encoding="utf-8"
    ))
    all_summaries.append(summary)
with open(out_path.parent/"combined_summary.json","w",encoding="utf-8") as f:
    json.dump(all_summaries, f, ensure_ascii=False, indent=2)

print("Merge complete. Final dataset at:", out_path)
