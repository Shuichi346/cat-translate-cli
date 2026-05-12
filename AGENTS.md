# AGENTS.md

Project instructions for coding agents working in this repository.

- Keep the Python translation server as the source of truth for model loading and translation behavior. The Node.js Web UI in `web/` should proxy to `cat-translate-server` rather than loading GGUF models directly.
- Preserve the Gradio-compatible backend request shape for Node proxy calls: `{ "data": [text, sourceLanguage, targetLanguage] }`.
- Use `npm run web` for the Node.js Web UI and `uv run ruff check .` plus `uv run mypy src` for Python validation after related changes.
