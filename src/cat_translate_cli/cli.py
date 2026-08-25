"""コマンドラインインターフェース"""

from __future__ import annotations

import argparse
import sys

from cat_translate_cli.client import (
    DEFAULT_SERVER_URL,
    ServerUnavailableError,
    translate_via_server,
)
from cat_translate_cli.translator import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL_FILENAME,
    DEFAULT_N_CTX,
    DEFAULT_N_GPU_LAYERS,
    DEFAULT_REPO_ID,
    download_model,
    load_model,
    normalize_language,
    translate,
)


def build_parser() -> argparse.ArgumentParser:
    """引数パーサーを構築する"""
    parser = argparse.ArgumentParser(
        prog="cat-translate",
        description="CAT-Translate-7b (GGUF) を使った日英・英日翻訳CLIツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "使用例:\n"
            "  cat-translate \"これは猫です。\"\n"
            "  cat-translate \"Hello, world!\" --to ja\n"
            "  cat-translate --file input.txt --from en --to ja\n"
            "  echo \"こんにちは\" | cat-translate\n"
            "  cat-translate \"猫\" --verbose\n"
            "\n"
            "サーバーモード:\n"
            "  サーバーへ接続できる場合は自動的にサーバー経由で翻訳します（高速）\n"
            "  サーバー起動: cat-translate-server\n"
            "  サーバーを使わない: cat-translate \"テキスト\" --no-server\n"
        ),
    )

    parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="翻訳するテキスト（省略時は --file または標準入力から読み取り）",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        default=None,
        help="翻訳するテキストファイルのパス",
    )
    parser.add_argument(
        "--from",
        dest="src_lang",
        type=str,
        default=None,
        metavar="LANG",
        help="原文の言語（ja / en / Japanese / English、省略時は自動判定）",
    )
    parser.add_argument(
        "--to",
        dest="tgt_lang",
        type=str,
        default=None,
        metavar="LANG",
        help="翻訳先の言語（ja / en / Japanese / English、省略時は自動判定）",
    )
    parser.add_argument(
        "--repo-id",
        type=str,
        default=DEFAULT_REPO_ID,
        help=f"Hugging Face リポジトリ ID（デフォルト: {DEFAULT_REPO_ID}）",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL_FILENAME,
        help=f"GGUF モデルファイル名（デフォルト: {DEFAULT_MODEL_FILENAME}）",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="ローカルの GGUF モデルファイルパス（指定時はダウンロードをスキップ）",
    )
    parser.add_argument(
        "--n-gpu-layers",
        type=int,
        default=DEFAULT_N_GPU_LAYERS,
        help=(
            f"GPU に載せるレイヤー数（デフォルト: {DEFAULT_N_GPU_LAYERS}、"
            "-1 で全レイヤー）"
        ),
    )
    parser.add_argument(
        "--n-ctx",
        type=int,
        default=DEFAULT_N_CTX,
        help=f"コンテキストウィンドウサイズ（デフォルト: {DEFAULT_N_CTX}）",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"生成する最大トークン数（デフォルト: {DEFAULT_MAX_TOKENS}）",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="モデル読み込みや llama.cpp の詳細ログを表示する",
    )
    parser.add_argument(
        "--server-url",
        type=str,
        default=DEFAULT_SERVER_URL,
        help=f"翻訳サーバーの URL（デフォルト: {DEFAULT_SERVER_URL}）",
    )
    parser.add_argument(
        "--no-server",
        action="store_true",
        help="サーバーを使わず、常にローカルでモデルを読み込んで翻訳する",
    )
    return parser


def get_input_text(args: argparse.Namespace) -> str:
    """引数・ファイル・標準入力からテキストを取得する"""
    if args.text is not None:
        return args.text

    if args.file is not None:
        try:
            with open(args.file, "r", encoding="utf-8") as file:
                return file.read().strip()
        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"ファイルが見つかりません: {args.file}"
            ) from error
        except OSError as error:
            raise OSError(
                f"ファイル読み込みに失敗しました: {error}"
            ) from error

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    raise ValueError(
        "翻訳するテキストを指定してください。"
        " 使い方: cat-translate \"テキスト\" または "
        "cat-translate --file ファイル.txt"
    )


def translate_local(args: argparse.Namespace, text: str) -> str:
    """ローカルでモデルを読み込んで翻訳する"""
    src_lang = normalize_language(args.src_lang) if args.src_lang else None
    tgt_lang = normalize_language(args.tgt_lang) if args.tgt_lang else None

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

    return translate(
        llm=llm,
        text=text,
        src_lang=src_lang,
        tgt_lang=tgt_lang,
        max_tokens=args.max_tokens,
    )


def translate_remote(args: argparse.Namespace, text: str) -> str:
    """サーバー経由で翻訳する"""
    src_lang = normalize_language(args.src_lang) if args.src_lang else None
    tgt_lang = normalize_language(args.tgt_lang) if args.tgt_lang else None

    return translate_via_server(
        text=text,
        src_lang=src_lang,
        tgt_lang=tgt_lang,
        server_url=args.server_url,
    )


def _requires_local_model(args: argparse.Namespace) -> bool:
    """サーバーへ渡せないモデル設定が指定されているか判定する。"""
    return (
        args.model_path is not None
        or args.repo_id != DEFAULT_REPO_ID
        or args.model != DEFAULT_MODEL_FILENAME
        or args.n_gpu_layers != DEFAULT_N_GPU_LAYERS
        or args.n_ctx != DEFAULT_N_CTX
        or args.max_tokens != DEFAULT_MAX_TOKENS
    )


def main() -> None:
    """メインエントリーポイント"""
    parser = build_parser()
    args = parser.parse_args()

    try:
        text = get_input_text(args)
        if not text:
            raise ValueError("空のテキストです。")

        use_remote = not args.no_server and not _requires_local_model(args)
        if use_remote:
            try:
                if args.verbose:
                    print(
                        f"サーバー経由で翻訳します ({args.server_url})",
                        file=sys.stderr,
                    )
                result = translate_remote(args, text)
            except ServerUnavailableError:
                if args.verbose:
                    print(
                        "サーバーが見つかりません。ローカルで翻訳します。",
                        file=sys.stderr,
                    )
                result = translate_local(args, text)
        else:
            if args.verbose and not args.no_server and _requires_local_model(args):
                print(
                    "モデル設定オプションが指定されたためローカルで翻訳します。",
                    file=sys.stderr,
                )
            result = translate_local(args, text)

    except KeyboardInterrupt:
        print("\n中断しました。", file=sys.stderr)
        sys.exit(130)
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
        print(f"エラー: {error}", file=sys.stderr)
        sys.exit(1)

    print(result)
