"""翻訳エンジン: GGUF モデルの読み込みと翻訳処理"""

import sys

from huggingface_hub import hf_hub_download
from llama_cpp import Llama


# Hugging Face リポジトリ ID（量子化 GGUF）
DEFAULT_REPO_ID = "mradermacher/CAT-Translate-7b-i1-GGUF"

# デフォルトモデルファイル名
DEFAULT_MODEL_FILENAME = "CAT-Translate-7b.i1-Q4_K_M.gguf"

# Apple Silicon (Metal) で全レイヤーを GPU に載せる
DEFAULT_N_GPU_LAYERS = -1

# コンテキストウィンドウサイズ
DEFAULT_N_CTX = 4096


def download_model(repo_id: str, filename: str) -> str:
    """Hugging Face Hub からモデルをダウンロードし、ローカルパスを返す"""
    print(f"モデルを準備中: {repo_id}/{filename}", file=sys.stderr)
    print("（初回はダウンロードに時間がかかります）", file=sys.stderr)

    local_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
    )

    print(f"モデル準備完了: {local_path}", file=sys.stderr)
    return local_path


def load_model(
    model_path: str,
    n_gpu_layers: int = DEFAULT_N_GPU_LAYERS,
    n_ctx: int = DEFAULT_N_CTX,
    verbose: bool = False,
) -> Llama:
    """GGUF モデルを読み込んで Llama インスタンスを返す"""
    print("モデルを読み込み中...", file=sys.stderr)

    llm = Llama(
        model_path=model_path,
        n_gpu_layers=n_gpu_layers,
        n_ctx=n_ctx,
        verbose=verbose,
    )

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
        # ひらがな・カタカナ・漢字・全角記号の範囲
        cp = ord(char)
        if (
            (0x3040 <= cp <= 0x309F)       # ひらがな
            or (0x30A0 <= cp <= 0x30FF)    # カタカナ
            or (0x4E00 <= cp <= 0x9FFF)    # CJK統合漢字
            or (0x3400 <= cp <= 0x4DBF)    # CJK統合漢字拡張A
            or (0xFF00 <= cp <= 0xFFEF)    # 全角英数・記号
            or (0x3000 <= cp <= 0x303F)    # CJK記号
        ):
            japanese_count += 1

    if total_count == 0:
        return "English"

    # 日本語文字が30%以上なら日本語と判定
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
    """テキストを翻訳する

    src_lang / tgt_lang が None の場合は自動判定する。
    """
    # 言語の自動判定
    if src_lang is None:
        src_lang = detect_language(text)
    if tgt_lang is None:
        tgt_lang = "English" if src_lang == "Japanese" else "Japanese"

    # CAT-Translate のプロンプト形式
    prompt = (
        f"Translate the following {src_lang} text "
        f"into {tgt_lang}.\n\n{text}"
    )

    messages = [
        {"role": "user", "content": prompt},
    ]

    # チャット形式で推論（GGUF にチャットテンプレートが含まれている）
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.1,
    )

    result = response["choices"][0]["message"]["content"]
    return result.strip()
