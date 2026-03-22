<table>
  <thead>
    <tr>
      <th style='text-align:center'><a href='README_en.md'>English</a></th>
      <th style='text-align:center'><a href='README.md'>日本語</a></th>
    </tr>
  </thead>
</table>

# cat-translate-cli

A CLI tool for Japanese-English and English-Japanese translation using the quantized GGUF model of [CAT-Translate-7b](https://huggingface.co/cyberagent/CAT-Translate-7b).

It supports Apple Silicon (Metal) and can run locally on Mac.

Using **Server Mode**, you can keep the model resident for fast translation from both browser and CLI.

## Requirements

- macOS (Apple Silicon recommended)
- Python 3.10 or later
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Xcode Command Line Tools (`xcode-select --install`)

## Installation

### Basic Installation (Note: This is CPU-only)

```bash
pip install cat-translate-cli
```

### Apple Silicon (Metal GPU) (recommended)

```bash
# リポジトリをクローン
git clone https://github.com/yourname/cat-translate-cli.git
cd cat-translate-cli

# Install with Metal (GPU) support
CMAKE_ARGS='-DGGML_METAL=on' uv sync

# Activate virtual environment
source .venv/bin/activate
```

> **Note**: `llama-cpp-python` requires C++ compilation.
> To use GPU on Apple Silicon, add `CMAKE_ARGS='-DGGML_METAL=on'`.

## Usage

### CLI (Command Line)

```bash
# Japanese → English (automatic language detection)
cat-translate '猫はとてもかわいいです。'

# English → Japanese (automatic language detection)
cat-translate 'Cats are very cute.'

# Specify target language (ja / en abbreviations available)
cat-translate 'Hello, world!' --to ja
cat-translate 'こんにちは' --to en

# Full names also work
cat-translate 'Hello, world!' --to Japanese

# Explicitly specify source language too
cat-translate 'Hello!' --from en --to ja

# Translate from file
cat-translate --file input.txt

# Pipe input
echo 'こんにちは世界' | cat-translate

# Redirect only translation results (no logs)
cat-translate '猫はかわいい' > output.txt
```

### Server Mode (Fast Translation)

When the server is started, the model remains resident, significantly speeding up CLI translation.
You can also translate from the browser using the Web UI.

```bash
# Terminal 1: Start server (initial model loading takes time on first run)
cat-translate-server

# Terminal 2: Translate with CLI (automatically uses server if running)
cat-translate '猫はとてもかわいいです。'

# Open Web UI in browser
# → http://127.0.0.1:7860
```

When the server is not running, it loads the model locally for translation as before.

```bash
# Always translate locally without using server
cat-translate '猫はかわいい' --no-server
```

### Main CLI Options

| Option | Description | Default |
|---|---|---|
| `--from LANG` | Source language (ja / en / Japanese / English) | Auto-detect |
| `--to LANG` | Target language (ja / en / Japanese / English) | Auto-detect |
| `--model` | GGUF filename | `CAT-Translate-7b.i1-Q4_K_M.gguf` |
| `--model-path` | Local GGUF file path | None (download from HF) |
| `--repo-id` | Hugging Face repository ID | `mradermacher/CAT-Translate-7b-i1-GGUF` |
| `--n-gpu-layers` | Number of layers to put on GPU | `-1` (all layers) |
| `--n-ctx` | Context window size | `4096` |
| `--max-tokens` | Maximum generation tokens | `2048` |
| `--verbose` | Show detailed logs | Off |
| `--server-url` | Translation server URL | `http://127.0.0.1:7860` |
| `--no-server` | Translate locally without using server | Off |

### Main Server Options

| Option | Description | Default |
|---|---|---|
| `--host` | Server host | `127.0.0.1` |
| `--port` | Server port | `7860` |
| `--model` | GGUF filename | `CAT-Translate-7b.i1-Q4_K_M.gguf` |
| `--model-path` | Local GGUF file path | None |
| `--n-gpu-layers` | Number of layers to put on GPU | `-1` |
| `--n-ctx` | Context window size | `4096` |
| `--max-tokens` | Maximum generation tokens | `2048` |
| `--verbose` | Show detailed logs | Off |

### Using Different Quantized Models

```bash
# Use lightweight model (Q2_K)
cat-translate 'こんにちは' --model CAT-Translate-7b.i1-Q2_K.gguf

# Use high-quality model (Q6_K)
cat-translate 'こんにちは' --model CAT-Translate-7b.i1-Q6_K.gguf
```

### Running on CPU Only

```bash
cat-translate 'こんにちは' --n-gpu-layers 0
```

### Troubleshooting

If something isn't working properly, add `--verbose` to check detailed logs.

```bash
cat-translate '猫はかわいい' --verbose
```

## About the Model

- **Original Model**: [cyberagent/CAT-Translate-7b](https://huggingface.co/cyberagent/CAT-Translate-7b) (MIT License)
- **GGUF Quantization**: [mradermacher/CAT-Translate-7b-i1-GGUF](https://huggingface.co/mradermacher/CAT-Translate-7b-i1-GGUF)
- **Default Quantization**: `i1-Q4_K_M` (approximately 4.6 GB, good balance of speed and quality)
- The model is automatically downloaded on first run (saved to `~/.cache/huggingface/`)

## License

MIT License