<table>
  <thead>
    <tr>
      <th style="text-align:center"><a href="README_en.md">English</a></th>
      <th style="text-align:center"><a href="README.md">日本語</a></th>
    </tr>
  </thead>
</table>

# cat-translate-cli

[CAT-Translate-7b](https://huggingface.co/cyberagent/CAT-Translate-7b) の量子化 GGUF モデルを使った、日英・英日翻訳の CLI ツールです。

Apple Silicon (Metal) に対応しており、Mac でローカル実行できます。

## 必要なもの

- macOS（Apple Silicon 推奨）
- Python 3.10 以上
- [uv](https://docs.astral.sh/uv/)（Python パッケージマネージャー）
- Xcode Command Line Tools（`xcode-select --install`）

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/yourname/cat-translate-cli.git
cd cat-translate-cli

# Metal（GPU）対応でインストール
CMAKE_ARGS="-DGGML_METAL=on" uv pip install -e .

# 仮想環境アクティブ
source .venv/bin/activate
```

> **注意**: `llama-cpp-python` は C++ のビルドが必要です。
> Apple Silicon で GPU を使うには `CMAKE_ARGS="-DGGML_METAL=on"` を付けてください。

## 使い方

```bash
# 日本語 → 英語（言語は自動判定）
cat-translate "猫はとてもかわいいです。"

# 英語 → 日本語（言語は自動判定）
cat-translate "Cats are very cute."

# 翻訳先の言語を指定（ja / en の短縮形が使えます）
cat-translate "Hello, world!" --to ja
cat-translate "こんにちは" --to en

# フルネームでも OK
cat-translate "Hello, world!" --to Japanese

# 原文の言語も明示的に指定
cat-translate "Hello!" --from en --to ja

# ファイルから翻訳
cat-translate --file input.txt

# パイプ入力
echo "こんにちは世界" | cat-translate

# 翻訳結果だけリダイレクト（ログは出ません）
cat-translate "猫はかわいい" > output.txt
```

### 主なオプション

| オプション | 説明 | デフォルト |
|---|---|---|
| `--from LANG` | 原文の言語（ja / en / Japanese / English） | 自動判定 |
| `--to LANG` | 翻訳先の言語（ja / en / Japanese / English） | 自動判定 |
| `--model` | GGUF ファイル名 | `CAT-Translate-7b.i1-Q4_K_M.gguf` |
| `--model-path` | ローカルの GGUF ファイルパス | なし（HF からダウンロード） |
| `--repo-id` | Hugging Face リポジトリ ID | `mradermacher/CAT-Translate-7b-i1-GGUF` |
| `--n-gpu-layers` | GPU に載せるレイヤー数 | `-1`（全レイヤー） |
| `--n-ctx` | コンテキストウィンドウサイズ | `4096` |
| `--max-tokens` | 最大生成トークン数 | `2048` |
| `--verbose` | モデル読み込み・llama.cpp の詳細ログを表示 | オフ |

### 別の量子化モデルを使う

```bash
# 軽量モデル（Q2_K）を使う場合
cat-translate "こんにちは" --model CAT-Translate-7b.i1-Q2_K.gguf

# 高品質モデル（Q6_K）を使う場合
cat-translate "こんにちは" --model CAT-Translate-7b.i1-Q6_K.gguf
```

### CPU のみで実行する場合

```bash
cat-translate "こんにちは" --n-gpu-layers 0
```

### トラブルシューティング

動作がおかしい場合は `--verbose` を付けて詳細ログを確認してください。

```bash
cat-translate "猫はかわいい" --verbose
```

## モデルについて

- **元モデル**: [cyberagent/CAT-Translate-7b](https://huggingface.co/cyberagent/CAT-Translate-7b)（MIT License）
- **GGUF 量子化**: [mradermacher/CAT-Translate-7b-i1-GGUF](https://huggingface.co/mradermacher/CAT-Translate-7b-i1-GGUF)
- **デフォルト量子化**: `i1-Q4_K_M`（約 4.6 GB、速度と品質のバランスが良い）
- 初回実行時にモデルが自動ダウンロードされます（`~/.cache/huggingface/` に保存）

## ライセンス

MIT License