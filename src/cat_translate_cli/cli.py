"""コマンドラインインターフェース"""

import argparse
import sys

from cat_translate_cli.translator import (
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
            '  echo "こんにちは" | cat-translate\n'
            "  cat-translate \"猫\" --verbose  # 詳細ログ表示\n"
        ),
    )

    parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="翻訳するテキスト（省略時は --file または標準入力から読み取り）",
    )

    parser.add_argument(
        "-f", "--file",
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
        help=f"GPU に載せるレイヤー数（デフォルト: {DEFAULT_N_GPU_LAYERS}、-1 で全レイヤー）",
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
        default=2048,
        help="生成する最大トークン数（デフォルト: 2048）",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="モデル読み込みや llama.cpp の詳細ログを表示する",
    )

    return parser


def get_input_text(args: argparse.Namespace) -> str:
    """引数・ファイル・標準入力からテキストを取得する"""
    if args.text is not None:
        return args.text

    if args.file is not None:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"エラー: ファイルが見つかりません: {args.file}", file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            print(f"エラー: ファイル読み込みに失敗: {e}", file=sys.stderr)
            sys.exit(1)

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    print("エラー: 翻訳するテキストを指定してください。", file=sys.stderr)
    print("使い方: cat-translate \"テキスト\" または cat-translate --file ファイル.txt", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    """メインエントリーポイント"""
    parser = build_parser()
    args = parser.parse_args()

    src_lang = normalize_language(args.src_lang) if args.src_lang else None
    tgt_lang = normalize_language(args.tgt_lang) if args.tgt_lang else None

    text = get_input_text(args)

    if not text:
        print("エラー: 空のテキストです。", file=sys.stderr)
        sys.exit(1)

    if args.model_path is not None:
        model_path = args.model_path
    else:
        model_path = download_model(
            args.repo_id, args.model, verbose=args.verbose,
        )

    llm = load_model(
        model_path=model_path,
        n_gpu_layers=args.n_gpu_layers,
        n_ctx=args.n_ctx,
        verbose=args.verbose,
    )

    result = translate(
        llm=llm,
        text=text,
        src_lang=src_lang,
        tgt_lang=tgt_lang,
        max_tokens=args.max_tokens,
    )

    print(result)
