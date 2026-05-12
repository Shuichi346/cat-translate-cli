#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${CAT_TRANSLATE_ENV_FILE:-"$ROOT_DIR/.env"}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

CAT_TRANSLATE_WEB_HOST="${CAT_TRANSLATE_WEB_HOST:-127.0.0.1}"
CAT_TRANSLATE_WEB_PORT="${CAT_TRANSLATE_WEB_PORT:-3000}"
CAT_TRANSLATE_SERVER_HOST="${CAT_TRANSLATE_SERVER_HOST:-127.0.0.1}"
CAT_TRANSLATE_SERVER_PORT="${CAT_TRANSLATE_SERVER_PORT:-7860}"
CAT_TRANSLATE_REPO_ID="${CAT_TRANSLATE_REPO_ID:-mradermacher/CAT-Translate-7b-i1-GGUF}"
CAT_TRANSLATE_MODEL="${CAT_TRANSLATE_MODEL:-CAT-Translate-7b.i1-Q6_K.gguf}"
CAT_TRANSLATE_N_GPU_LAYERS="${CAT_TRANSLATE_N_GPU_LAYERS:--1}"
CAT_TRANSLATE_N_CTX="${CAT_TRANSLATE_N_CTX:-4096}"
CAT_TRANSLATE_MAX_TOKENS="${CAT_TRANSLATE_MAX_TOKENS:-2048}"
CAT_TRANSLATE_BACKEND_URL="${CAT_TRANSLATE_BACKEND_URL:-http://$CAT_TRANSLATE_SERVER_HOST:$CAT_TRANSLATE_SERVER_PORT}"

backend_pid=""

cleanup() {
  if [[ -n "$backend_pid" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    kill "$backend_pid" 2>/dev/null || true
    wait "$backend_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

backend_ready() {
  curl -fsS "$CAT_TRANSLATE_BACKEND_URL/gradio_api/info" >/dev/null 2>&1
}

cd "$ROOT_DIR"

if backend_ready; then
  echo "Using existing CAT-Translate backend: $CAT_TRANSLATE_BACKEND_URL"
else
  backend_args=(
    --host "$CAT_TRANSLATE_SERVER_HOST"
    --port "$CAT_TRANSLATE_SERVER_PORT"
    --n-gpu-layers "$CAT_TRANSLATE_N_GPU_LAYERS"
    --n-ctx "$CAT_TRANSLATE_N_CTX"
    --max-tokens "$CAT_TRANSLATE_MAX_TOKENS"
  )

  if [[ -n "${CAT_TRANSLATE_MODEL_PATH:-}" ]]; then
    backend_args+=(--model-path "$CAT_TRANSLATE_MODEL_PATH")
  else
    backend_args+=(--repo-id "$CAT_TRANSLATE_REPO_ID" --model "$CAT_TRANSLATE_MODEL")
  fi

  echo "Starting CAT-Translate backend: $CAT_TRANSLATE_BACKEND_URL"
  uv run cat-translate-server "${backend_args[@]}" &
  backend_pid="$!"

  for _ in {1..180}; do
    if backend_ready; then
      break
    fi
    if ! kill -0 "$backend_pid" 2>/dev/null; then
      wait "$backend_pid"
    fi
    sleep 1
  done

  if ! backend_ready; then
    echo "Timed out waiting for CAT-Translate backend: $CAT_TRANSLATE_BACKEND_URL" >&2
    exit 1
  fi
fi

echo "CAT-Translate Web UI: http://$CAT_TRANSLATE_WEB_HOST:$CAT_TRANSLATE_WEB_PORT"
HOST="$CAT_TRANSLATE_WEB_HOST" \
PORT="$CAT_TRANSLATE_WEB_PORT" \
CAT_TRANSLATE_BACKEND_URL="$CAT_TRANSLATE_BACKEND_URL" \
npm run web
