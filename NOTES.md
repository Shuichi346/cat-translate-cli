# Notes

## 2026-05-12

- Added the Node.js Web UI as an additive layer over the existing Python Gradio translation server instead of duplicating model loading in Node.
- Verified the Node proxy contract against the Gradio-style `/api/translate` response shape with a temporary mock backend because the default GGUF model was not cached locally.
- Confirmed that the UI reports a clean JSON/visible error when the Python translation backend is unavailable.
- Fixed the server/client contract for Gradio 6.9.0: direct event calls live under `/gradio_api/run/translate`, while `/api/translate` returns 404.
- Added `scripts/start-web-ui.sh` to load `.env`, select a GGUF model, start the Python backend, and launch the Node Web UI at `http://127.0.0.1:3000`.
