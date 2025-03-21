import json
import logging
import os
import re

from pythainlp.tokenize import word_tokenize, sent_tokenize

from third_party.deep_phonemizer.phonemizer import Phonemizer

logging.disable(logging.CRITICAL)

dp_dir = os.path.dirname(os.path.abspath(__file__))
phonemizer_model = dp_dir + "/ckpts/best_model.pt"
phonemizer = Phonemizer.from_checkpoint(phonemizer_model)
phonemizer.predictor.model = phonemizer.predictor.model.half()


def g2p(text, lang='th', token_sep='-', punctuation=".", verbose=False):
    # chunking into sentences
    sentences = sent_tokenize(text, engine="crfcut")
    results = {}
    for index, sentence in enumerate(sentences):
        tokens = word_tokenize(re.sub(r'\s+', ' ', sentence.strip()), engine="attacut")
        tokens_ph = [
            token_sep.join(phonemizer(t, lang).split(" "))
            if not t.isspace() else ""
            for t in tokens
        ]
        results[index] = {
            "sentence": sentence,
            "sentence_ph": f"{' '.join(tokens_ph).replace('  ', ' ')}{punctuation}",
            "tokens": [[t, ph] for t, ph in zip(tokens, tokens_ph)],
            # "tokens_ph": ,
        }
    if verbose:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    return " ".join([value["sentence_ph"] for key, value in results.items()])


if __name__ == "__main__":
    text = '''ที่เกิดเหตุกุฎิพระชั้นเดียว ภายในห้องพบศพ พระ อายุ 46 ปี สภาพศพนอนคว่ำหน้า จมกองเลือด มีบาดแผลถูกสุนัขกัดข้อมือขาดหายไม่พบชิ้นส่วน และกระโหลกศีรษะด้านขวาถูกกัดแทะจนถึงกระโหลก เสียชีวิตมาแล้วประมาณ 2 วัน'''
    tokens_phoneme = g2p(text, verbose=False)
    print("input:\n", text)
    print("output:\n", tokens_phoneme)
