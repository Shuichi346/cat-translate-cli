"""Gradio Web UI サーバー: モデルを常駐させてブラウザ・CLI から翻訳"""

from __future__ import annotations

import argparse
import sys
import threading

import gradio as gr
from llama_cpp import Llama

from cat_translate_cli.translator import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL_FILENAME,
    DEFAULT_N_CTX,
    DEFAULT_N_GPU_LAYERS,
    DEFAULT_REPO_ID,
    detect_language,
    download_model,
    load_model,
    normalize_language,
    translate,
)

# 言語選択肢（UIドロップダウン用）
LANGUAGE_CHOICES = ["自動判定", "Japanese", "English"]
_TRANSLATION_CONCURRENCY_ID = "cat-translate-model"


def _resolve_language(value: str) -> str | None:
    """UI の選択値を translator の引数形式に変換する"""
    if value == "自動判定":
        return None
    return normalize_language(value)


def build_parser() -> argparse.ArgumentParser:
    """サーバー用の引数パーサーを構築する"""
    parser = argparse.ArgumentParser(
        prog="cat-translate-server",
        description="CAT-Translate 翻訳サーバー（Gradio Web UI）",
    )
    parser.add_argument("--host", type=str, default="127.0.0.1", help="サーバーのホスト（デフォルト: 127.0.0.1）")
    parser.add_argument("--port", type=int, default=7860, help="サーバーのポート（デフォルト: 7860）")
    parser.add_argument("--repo-id", type=str, default=DEFAULT_REPO_ID, help=f"Hugging Face リポジトリ ID（デフォルト: {DEFAULT_REPO_ID}）")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_FILENAME, help=f"GGUF モデルファイル名（デフォルト: {DEFAULT_MODEL_FILENAME}）")
    parser.add_argument("--model-path", type=str, default=None, help="ローカルの GGUF モデルファイルパス")
    parser.add_argument("--n-gpu-layers", type=int, default=DEFAULT_N_GPU_LAYERS, help=f"GPU に載せるレイヤー数（デフォルト: {DEFAULT_N_GPU_LAYERS}）")
    parser.add_argument("--n-ctx", type=int, default=DEFAULT_N_CTX, help=f"コンテキストウィンドウサイズ（デフォルト: {DEFAULT_N_CTX}）")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS, help=f"最大生成トークン数（デフォルト: {DEFAULT_MAX_TOKENS}）")
    parser.add_argument("--verbose", action="store_true", help="詳細ログを表示する")
    return parser


def create_app(llm: Llama, max_tokens: int = DEFAULT_MAX_TOKENS) -> gr.Blocks:
    """Gradio アプリケーションを構築する"""
    model_lock = threading.Lock()

    def do_translate(
        text: str,
        src_lang_choice: str,
        tgt_lang_choice: str,
    ) -> str:
        """翻訳を実行する（Gradio コールバック）"""
        if not text or not text.strip():
            return ""

        src_lang = _resolve_language(src_lang_choice)
        tgt_lang = _resolve_language(tgt_lang_choice)

        # llama.cpp の同一コンテキストを複数リクエストから同時利用しない。
        with model_lock:
            return translate(
                llm=llm,
                text=text.strip(),
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                max_tokens=max_tokens,
            )

    def swap_languages(
        src_lang_choice: str,
        tgt_lang_choice: str,
        input_text: str,
        output_text: str,
    ) -> tuple[str, str, str, str]:
        """原文と訳文、言語設定を入れ替える"""
        new_src = tgt_lang_choice
        new_tgt = src_lang_choice
        return new_src, new_tgt, output_text, input_text

    def auto_detect_label(text: str, src_lang_choice: str) -> str:
        """入力テキストから検出された言語をラベルで表示する"""
        if not text or not text.strip():
            return ""
        if src_lang_choice != "自動判定":
            return ""
        detected = detect_language(text.strip())
        return f"検出: {detected}"

    with gr.Blocks(title="CAT-Translate") as app:
        gr.Markdown("# CAT-Translate — 日英・英日翻訳")
        gr.Markdown(
            "モデル: [CAT-Translate-7b](https://huggingface.co/cyberagent/CAT-Translate-7b)"
            "（GGUF 量子化版）"
        )

        with gr.Row():
            src_lang = gr.Dropdown(
                choices=LANGUAGE_CHOICES,
                value="自動判定",
                label="原文の言語",
                interactive=True,
            )
            swap_btn = gr.Button("⇄ 入れ替え", scale=0)
            tgt_lang = gr.Dropdown(
                choices=LANGUAGE_CHOICES,
                value="自動判定",
                label="翻訳先の言語",
                interactive=True,
            )

        with gr.Row():
            with gr.Column():
                input_text = gr.Textbox(
                    label="原文",
                    placeholder="翻訳したいテキストを入力してください...",
                    lines=8,
                )
                detected_label = gr.Textbox(
                    label="言語検出",
                    interactive=False,
                    lines=1,
                )
            with gr.Column():
                output_text = gr.Textbox(
                    label="翻訳結果",
                    lines=8,
                    interactive=False,
                )

        translate_btn = gr.Button("翻訳", variant="primary")

        translate_btn.click(
            fn=do_translate,
            inputs=[input_text, src_lang, tgt_lang],
            outputs=output_text,
            api_name="translate",
            concurrency_limit=1,
            concurrency_id=_TRANSLATION_CONCURRENCY_ID,
        )
        input_text.submit(
            fn=do_translate,
            inputs=[input_text, src_lang, tgt_lang],
            outputs=output_text,
            concurrency_limit=1,
            concurrency_id=_TRANSLATION_CONCURRENCY_ID,
        )
        swap_btn.click(
            fn=swap_languages,
            inputs=[src_lang, tgt_lang, input_text, output_text],
            outputs=[src_lang, tgt_lang, input_text, output_text],
        )
        input_text.change(
            fn=auto_detect_label,
            inputs=[input_text, src_lang],
            outputs=detected_label,
        )

    return app


def main() -> None:
    """サーバーのエントリーポイント"""
    parser = build_parser()
    args = parser.parse_args()

    print("モデルを読み込み中（初回のみ時間がかかります）...", file=sys.stderr)

    try:
        if args.model_path is not None:
            model_path = args.model_path
        else:
            model_path = download_model(
                args.repo_id,
                args.model,
                verbose=args.verbose,
            )

        llm = load_model(
            model_path=model_path,
            n_gpu_layers=args.n_gpu_layers,
            n_ctx=args.n_ctx,
            verbose=args.verbose,
        )
    except (RuntimeError, OSError) as error:
        print(f"エラー: {error}", file=sys.stderr)
        sys.exit(1)

    print("モデル読み込み完了。サーバーを起動します。", file=sys.stderr)

    app = create_app(llm=llm, max_tokens=args.max_tokens)
    app.launch(
        server_name=args.host,
        server_port=args.port,
    )
