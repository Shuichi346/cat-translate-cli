<table>
  <thead>
    <tr>
      <th style='text-align:center'><a href='README_en.md'>English</a></th>
      <th style='text-align:center'><a href='README.md'>日本語</a></th>
    </tr>
  </thead>
</table>

# cat-translate-cli

A CLI tool for Japanese-to-English and English-to-Japanese translation using a quantized GGUF model of [CAT-Translate-7b](https://huggingface.co/cyberagent/CAT-Translate-7b).

Supports Apple Silicon (Metal) and can be run locally on a Mac.

Using **server mode**, you can keep the model resident and translate quickly from both the browser and the CLI.

## Requirements

- macOS (Apple Silicon recommended)
- Python 3.10 or later
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Xcode Command Line Tools (`xcode-select --install`)

## Installation

### Basic Installation (Note: this is CPU-only)
```bash
pip install cat-translate-cli
```

### For use with Apple Silicon (Metal GPU) (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourname/cat-translate-cli.git
cd cat-translate-cli

# Install with Metal (GPU) support
CMAKE_ARGS='-DGGML_METAL=on' uv sync

# Activate the virtual environment
source .venv/bin/activate
```

> **Note**: `llama-cpp-python` requires a C++ build.
> To use the GPU on Apple Silicon, add `CMAKE_ARGS='-DGGML_METAL=on'`.

## Usage

### CLI (Command Line)

```bash
# Japanese → English (language is auto-detected)
cat-translate '猫はとてもかわいいです。'

# English → Japanese (language is auto-detected)
cat-translate 'Cats are very cute.'

# Specify the target language (shorthand ja / en can be used)
cat-translate 'Hello, world!' --to ja
cat-translate 'こんにちは' --to en

# Full name also works
cat-translate 'Hello, world!' --to Japanese

# Explicitly specify the source language as well
cat-translate 'Hello!' --from en --to ja

# Translate from a file
cat-translate --file input.txt

# Pipe input
echo 'こんにちは世界' | cat-translate

# Redirect only the translation result (no log output)
cat-translate '猫はかわいい' > output.txt
```

### Server Mode (Fast Translation)

Starting a server keeps the model resident, which greatly speeds up CLI translation.
You can also translate via Web UI from a browser.

```bash
# Terminal 1: Start the server (the first time, model loading will take some time)
cat-translate-server

# Terminal 2: Translate via CLI (automatically uses the server if it is running)
cat-translate '猫はとてもかわいいです。'

# Open the Web UI in the browser
# → http://127.0.0.1:7860
```

### Node.js Web UI Mode

Using the existing Python translation server as a backend, you can translate from a lightweight Node.js / Express Web UI.

```bash
# Install Node.js dependencies
npm install

# Copy .env.example and choose a model if needed
cp .env.example .env

# Start the Python translation server and Node.js Web UI
npm run start:web-ui

# Open the Node.js Web UI in the browser
# → http://127.0.0.1:3000
```

The Start Web UI script starts the Python server at `http://127.0.0.1:7860` by default,
then starts the Node.js Web UI at `http://127.0.0.1:3000`.
You can change this via environment variables as needed.

```bash
CAT_TRANSLATE_MODEL=CAT-Translate-7b.i1-Q4_K_M.gguf npm run start:web-ui
```

If the server is not running, it will load the model locally and translate as usual.

```bash
# Always translate locally without using the server
cat-translate '猫はかわいい' --no-server
```

### Main Options (CLI)

| Option | Description | Default |
|---|---|---|
| `--from LANG` | Source language (ja / en / Japanese / English) | Auto-detect |
| `--to LANG` | Target language (ja / en / Japanese / English) | Auto-detect |
| `--model` | GGUF file name | `CAT-Translate-7b.i1-Q4_K_M.gguf` |
| `--model-path` | Local GGUF file path | None (downloaded from HF) |
| `--repo-id` | Hugging Face repository ID | `mradermacher/CAT-Translate-7b-i1-GGUF` |
| `--n-gpu-layers` | Number of layers to offload to GPU | `-1` (all layers) |
| `--n-ctx` | Context window size | `4096` |
| `--max-tokens` | Maximum number of tokens to generate | `2048` |
| `--verbose` | Show detailed logs | Off |
| `--server-url` | Translation server URL | `http://127.0.0.1:7860` |
| `--no-server` | Translate locally without using the server | Off |

### Main Options (Server)

| Option | Description | Default |
|---|---|---|
| `--host` | Server host | `127.0.0.1` |
| `--port` | Server port | `7860` |
| `--model` | GGUF file name | `CAT-Translate-7b.i1-Q4_K_M.gguf` |
| `--model-path` | Local GGUF file path | None |
| `--n-gpu-layers` | Number of layers to offload to GPU | `-1` |
| `--n-ctx` | Context window size | `4096` |
| `--max-tokens` | Maximum number of tokens to generate | `2048` |
| `--verbose` | Show detailed logs | Off |

### Node.js Web UI Environment Variables

| Environment Variable | Description | Default |
|---|---|---|
| `HOST` | Node.js Web UI host | `127.0.0.1` |
| `PORT` | Node.js Web UI port | `3000` |
| `CAT_TRANSLATE_BACKEND_URL` | Python translation server URL | `http://127.0.0.1:7860` |

### Using a Different Quantized Model

```bash
# Using a lightweight model (Q2_K)
cat-translate 'こんにちは' --model CAT-Translate-7b.i1-Q4_K_M.gguf

# Using a high-quality model (Q6_K)
cat-translate 'こんにちは' --model CAT-Translate-7b.i1-Q6_K.gguf
```

### Running on CPU Only

```bash
cat-translate 'こんにちは' --n-gpu-layers 0
```

### Troubleshooting

If something seems wrong, add `--verbose` to check the detailed logs.

```bash
cat-translate '猫はかわいい' --verbose
```

## About the Model

- **Base model**: [cyberagent/CAT-Translate-7b](https://huggingface.co/cyberagent/CAT-Translate-7b) (MIT License)
- **GGUF quantization**: [mradermacher/CAT-Translate-7b-i1-GGUF](https://huggingface.co/mradermacher/CAT-Translate-7b-i1-GGUF)
- **Default quantization**: `i1-Q4_K_M` (approx. 4.6 GB, good balance of speed and quality)
- The model is automatically downloaded on the first run (saved to `~/.cache/huggingface/`)

## License

MIT License
