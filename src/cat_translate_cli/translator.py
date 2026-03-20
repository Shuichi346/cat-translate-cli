"""翻訳エンジン: GGUF モデルの読み込みと翻訳処理"""

from __future__ import annotations

import ctypes
import sys
from typing import Any

import llama_cpp
from huggingface_hub import hf_hub_download
from llama_cpp import Llama


DEFAULT_REPO_ID = "mradermacher/CAT-Translate-7b-i1-GGUF"
DEFAULT_MODEL_FILENAME = "CAT-Translate-7b.i1-Q4_K_M.gguf"
DEFAULT_N_GPU_LAYERS = -1
DEFAULT_N_CTX = 4096
DEFAULT_MAX_TOKENS = 2048

LANGUAGE_ALIASES = {
    "ja": "Japanese",
    "jp": "Japanese",
    "japanese": "Japanese",
    "en": "English",
    "eng": "English",
    "english": "English",
}

VALID_LANGUAGE_INPUTS = ["ja", "en", "Japanese", "English"]

_LLAMA_LOG_CALLBACK: Any | None = None


def suppress_llama_log() -> None:
    """llama.cpp の C レベルのログ出力を無効化する"""
    global _LLAMA_LOG_CALLBACK

    log_callback_type = ctypes.CFUNCTYPE(
        None,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_void_p,
    )

    def _null_log(_level: int, _text: bytes | None, _user_data: Any) -> None:
        return None

    _LLAMA_LOG_CALLBACK = log_callback_type(_null_log)

    try:
        llama_cpp.llama_cpp.llama_log_set(
            _LLAMA_LOG_CALLBACK,
            ctypes.c_void_p(0),
        )
    except AttributeError:
        pass


def normalize_language(value: str) -> str:
    """言語の短縮形・表記揺れを正式名に変換する"""
    normalized = LANGUAGE_ALIASES.get(value.lower())
    if normalized is None:
        valid = ", ".join(VALID_LANGUAGE_INPUTS)
        raise ValueError(
            f"不明な言語 '{value}' です（指定可能: {valid}）"
        )
    return normalized


def download_model(
    repo_id: str,
    filename: str,
    verbose: bool = False,
) -> str:
    """Hugging Face Hub からモデルをダウンロードし、ローカルパスを返す"""
    if verbose:
        print(f"モデルを準備中: {repo_id}/{filename}", file=sys.stderr)

    try:
        local_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
        )
    except Exception as error:
        raise RuntimeError(
            f"モデルの準備に失敗しました: {repo_id}/{filename}: {error}"
        ) from error

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

    try:
        llm = Llama(
            model_path=model_path,
            n_gpu_layers=n_gpu_layers,
            n_ctx=n_ctx,
            verbose=verbose,
        )
    except Exception as error:
        raise RuntimeError(
            f"モデル読み込みに失敗しました: {model_path}: {error}"
        ) from error

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
        code_point = ord(char)

        if (
            0x3040 <= code_point <= 0x309F
            or 0x30A0 <= code_point <= 0x30FF
            or 0x4E00 <= code_point <= 0x9FFF
            or 0x3400 <= code_point <= 0x4DBF
            or 0xFF00 <= code_point <= 0xFFEF
            or 0x3000 <= code_point <= 0x303F
        ):
            japanese_count += 1

    if total_count == 0:
        return "English"

    if japanese_count / total_count >= 0.3:
        return "Japanese"

    return "English"


def extract_translation_content(response: Any) -> str:
    """chat completion の応答から翻訳結果を安全に取り出す"""
    if not isinstance(response, dict):
        raise RuntimeError("モデル応答の形式が不正です。")

    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("モデルから応答を取得できませんでした。")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise RuntimeError("モデル応答の形式が不正です。")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("モデル応答の形式が不正です。")

    content = message.get("content")
    if not isinstance(content, str):
        raise RuntimeError("モデル応答に翻訳結果が含まれていません。")

    result = content.strip()
    if not result:
        raise RuntimeError("翻訳結果が空です。")

    return result


def translate(
    llm: Llama,
    text: str,
    src_lang: str | None = None,
    tgt_lang: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """テキストを翻訳する"""
    if src_lang is None:
        src_lang = detect_language(text)

    if tgt_lang is None:
        tgt_lang = "English" if src_lang == "Japanese" else "Japanese"

    prompt = (
        f"Translate the following {src_lang} text into {tgt_lang}.\n\n"
        f"{text}"
    )

    messages: Any = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    try:
        response = llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.1,
        )
    except Exception as error:
        raise RuntimeError(f"翻訳に失敗しました: {error}") from error

    return extract_translation_content(response)
