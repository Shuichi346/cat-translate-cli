# Notes

## 2026-05-12

- Added the Node.js Web UI as an additive layer over the existing Python Gradio translation server instead of duplicating model loading in Node.
- Verified the Node proxy contract against the Gradio-style `/api/translate` response shape with a temporary mock backend because the default GGUF model was not cached locally.
- Confirmed that the UI reports a clean JSON/visible error when the Python translation backend is unavailable.
