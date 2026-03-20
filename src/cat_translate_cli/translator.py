"""翻訳エンジン: GGUF モデルの読み込みと翻訳処理"""

import ctypes
import sys

from huggingface_hub import hf_hub_download
from llama_cpp import Llama
import llama_cpp


# Hugging Face リポジトリ ID（量子化 GGUF）
DEFAULT_REPO_ID = "mradermacher/CAT-Translate-7b-i1-GGUF"

# デフォルトモデルファイル名
DEFAULT_MODEL_FILENAME = "CAT-Translate-7b.i1-Q4_K_M.gguf"

# Apple Silicon (Metal) で全レイヤーを GPU に載せる
DEFAULT_N_GPU_LAYERS = -1

# コンテキストウィンドウサイズ
DEFAULT_N_CTX = 4096

# 言語の短縮形 → 正式名の対応表
LANGUAGE_ALIASES = {
    "ja": "Japanese",
    "jp": "Japanese",
    "japanese": "Japanese",
    "en": "English",
    "eng": "English",
    "english": "English",
}

# 入力で受け付ける言語名の一覧（ヘルプ表示用）
VALID_LANGUAGE_INPUTS = ["ja", "en", "Japanese", "English"]


def suppress_llama_log() -> None:
    """llama.cpp の C レベルのログ出力を無効化する"""
    # llama.cpp の内部ログコールバックを空関数に差し替える
    # これにより ggml_metal_init 等のメッセージが抑制される
    log_callback_type = ctypes.CFUNCTYPE(
        None,
        ctypes.c_int,       # level
        ctypes.c_char_p,    # text
        ctypes.c_void_p,    # user_data
    )

    def _null_log(level, text, user_data):
        pass

    # コールバックを保持（GC で回収されないようにする）
    suppress_llama_log._callback = log_callback_type(_null_log)

    try:
        llama_cpp.llama_cpp.llama_log_set(
            suppress_llama_log._callback,
            ctypes.c_void_p(0),
        )
    except AttributeError:
        # llama_log_set が存在しないバージョンの場合は無視
        pass


def normalize_language(value: str) -> str:
    """言語の短縮形・表記揺れを正式名に変換する"""
    normalized = LANGUAGE_ALIASES.get(value.lower())
    if normalized is None:
        valid = ", ".join(VALID_LANGUAGE_INPUTS)
        print(
            f"エラー: 不明な言語 '{value}'（指定可能: {valid}）",
            file=sys.stderr,
        )
        sys.exit(1)
    return normalized


def download_model(
    repo_id: str,
    filename: str,
    verbose: bool = False,
) -> str:
    """Hugging Face Hub からモデルをダウンロードし、ローカルパスを返す"""
    if verbose:
        print(f"モデルを準備中: {repo_id}/{filename}", file=sys.stderr)

    local_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
    )

    if verbose:
        print(f"モデル準備完了: {local_path}", file=sys.stderr)
    return local_path


def load_model(
    model_path: str,
    n_gpu_layers: int = DEFAULT_N_GPU_LAYERS,
    n_ctx: int = DEFAULT_N_CTX,
    verbose: bool = False,
) -> Llama:
    """GGUF モデルを読み込んで Llama インスタンスを返す"""
    if not verbose:
        suppress_llama_log()

    if verbose:
        print("モデルを読み込み中...", file=sys.stderr)

    llm = Llama(
        model_path=model_path,
        n_gpu_layers=n_gpu_layers,
        n_ctx=n_ctx,
        verbose=verbose,
    )

    if verbose:
        print("モデル読み込み完了", file=sys.stderr)
    return llm


def detect_language(text: str) -> str:
    """テキストの言語を簡易判定する（日本語 or 英語）"""
    japanese_count = 0
    total_count = 0

    for char in text:
        if char.isspace() or char in ".,!?;:\"'()-":
            continue
        total_count += 1
        cp = ord(char)
        if (
            (0x3040 <= cp <= 0x309F)
            or (0x30A0 <= cp <= 0x30FF)
            or (0x4E00 <= cp <= 0x9FFF)
            or (0x3400 <= cp <= 0x4DBF)
            or (0xFF00 <= cp <= 0xFFEF)
            or (0x3000 <= cp <= 0x303F)
        ):
            japanese_count += 1

    if total_count == 0:
        return "English"

    if japanese_count / total_count >= 0.3:
        return "Japanese"
    return "English"


def translate(
    llm: Llama,
    text: str,
    src_lang: str | None = None,
    tgt_lang: str | None = None,
    max_tokens: int = 2048,
) -> str:
    """テキストを翻訳する"""
    if src_lang is None:
        src_lang = detect_language(text)
    if tgt_lang is None:
        tgt_lang = "English" if src_lang == "Japanese" else "Japanese"

    prompt = (
        f"Translate the following {src_lang} text "
        f"into {tgt_lang}.\n\n{text}"
    )

    messages = [
        {"role": "user", "content": prompt},
    ]

    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.1,
    )

    result = response["choices"][0]["message"]["content"]
    return result.strip()
