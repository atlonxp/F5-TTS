import json
import os
import re

import requests
from pythainlp.tokenize import word_tokenize, sent_tokenize

Apikey = os.environ['AI4THAI_API']
external_g2p = 'https://api.aiforthai.in.th/vaja9/text2phoneme'
internal_g2p = 'http://10.223.72.14:8623/text2phoneme'


def g2p_api(text, url_g2p=internal_g2p):
    phoneme = None
    response = requests.post(
        url_g2p,
        json={'text': text},
        headers={
            'Apikey': Apikey,
            'Content-Type': 'application/json'
        }
    )
    if (response.json()['status'] == 'success'):
        phoneme = response.json()['ta_data']['phoneme']
    return phoneme


def g2p(text, lang='th', token_sep='-', punctuation=".", verbose=False):
    # chunking into sentences
    sentences = sent_tokenize(text, engine="crfcut")
    results = {}
    for index, sentence in enumerate(sentences):
        tokens = word_tokenize(re.sub(r'\s+', ' ', sentence.strip()), engine="attacut")

        tokens_ph_ = g2p_api(sentence)
        if tokens_ph_ is None:
            tokens_ph_ = ["" for t in tokens]
        tokens_ph = [
            token_sep.join(tokens_ph_.split(" "))
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
