import os
import random
import torch
from safetensors.torch import load_file, save_file

from importlib.resources import files
from cached_path import cached_path

path_data = str(files("f5_tts").joinpath("../../data"))
path_project_ckpts = str(files("f5_tts").joinpath("../../ckpts"))

def expand_model_embeddings(ckpt_path, new_ckpt_path, num_new_tokens=42):
    seed = 666
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    if ckpt_path.endswith(".safetensors"):
        ckpt = load_file(ckpt_path, device="cpu")
        ckpt = {"ema_model_state_dict": ckpt}
    elif ckpt_path.endswith(".pt"):
        ckpt = torch.load(ckpt_path, map_location="cpu")

    ema_sd = ckpt.get("ema_model_state_dict", {})
    embed_key_ema = "ema_model.transformer.text_embed.text_embed.weight"
    old_embed_ema = ema_sd[embed_key_ema]

    vocab_old = old_embed_ema.size(0)
    embed_dim = old_embed_ema.size(1)
    vocab_new = vocab_old + num_new_tokens

    def expand_embeddings(old_embeddings):
        new_embeddings = torch.zeros((vocab_new, embed_dim))
        new_embeddings[:vocab_old] = old_embeddings
        new_embeddings[vocab_old:] = torch.randn((num_new_tokens, embed_dim))
        return new_embeddings

    ema_sd[embed_key_ema] = expand_embeddings(ema_sd[embed_key_ema])

    if new_ckpt_path.endswith(".safetensors"):
        save_file(ema_sd, new_ckpt_path)
    elif new_ckpt_path.endswith(".pt"):
        torch.save(ckpt, new_ckpt_path)

    return vocab_new
    
def vocab_extend(project_name, model_type="F5TTS_v1_Base"):
    name_project = project_name
    path_project = os.path.join(path_data, name_project)
    file_vocab_project = os.path.join(path_project, "vocab.txt")

    file_vocab = os.path.join(path_data, "Emilia_ZH_EN_pinyin/vocab.txt")
    if not os.path.isfile(file_vocab):
        return f"the file {file_vocab} not found !"

    # project vocab
    symbols = []
    with open(file_vocab_project, 'r') as f:
        data = f.read()
        symbols = data.split("\n")
    if symbols == []:
        return "Symbols to extend not found."
    # print(f"project vocab: {len(symbols)}")
    
    # F5 v1 base vocab
    with open(file_vocab, "r", encoding="utf-8-sig") as f:
        data = f.read()
        vocab = data.split("\n")
    vocab_check = set(vocab)
    # print(f"project vocab: {len(vocab_check)}")

    miss_symbols = []
    for item in symbols:
        item = item.replace(" ", "")
        if item in vocab_check:
            continue
        miss_symbols.append(item)

    if miss_symbols == []:
        return "Symbols are okay no need to extend."
    # print(f"missing vocab: {len(miss_symbols)}")

    size_vocab = len(vocab)
    vocab.pop()
    for item in miss_symbols:
        vocab.append(item)
    vocab.append("")
    print(f"project vocab: {len(vocab)}")

    # we have done this manually, no need to rewrite this again
    # with open(file_vocab_project, "w", encoding="utf-8") as f:
    #     f.write("\n".join(vocab))

    if model_type == "F5TTS_v1_Base":
        ckpt_path = str(cached_path("hf://SWivid/F5-TTS/F5TTS_v1_Base/model_1250000.safetensors"))
    elif model_type == "F5TTS_Base":
        ckpt_path = str(cached_path("hf://SWivid/F5-TTS/F5TTS_Base/model_1200000.pt"))
    elif model_type == "E2TTS_Base":
        ckpt_path = str(cached_path("hf://SWivid/E2-TTS/E2TTS_Base/model_1200000.pt"))

    vocab_size_new = len(miss_symbols)

    dataset_name = name_project.replace("_pinyin", "").replace("_char", "")
    new_ckpt_path = os.path.join(path_project_ckpts, dataset_name)
    os.makedirs(new_ckpt_path, exist_ok=True)

    # Add pretrained_ prefix to model when copying for consistency with finetune_cli.py
    new_ckpt_file = os.path.join(new_ckpt_path, "pretrained_" + os.path.basename(ckpt_path))

    size = expand_model_embeddings(ckpt_path, new_ckpt_file, num_new_tokens=vocab_size_new)

    vocab_new = "\n".join(miss_symbols)
    print(f"vocab old size : {size_vocab}\nvocab new size : {size}\nvocab add : {vocab_size_new}\nnew symbols :\n{vocab_new}")


if __name__ == "__main__":
    project_name = "custom_th_en_zh_pinyin"
    vocab_extend(project_name)
