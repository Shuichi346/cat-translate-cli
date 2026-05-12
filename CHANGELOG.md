# Changelog

## Unreleased

- Added a Node.js Web UI mode that serves a static translator UI with Express and proxies translation requests to the existing Python `cat-translate-server` backend.
- Added a Start Web UI script and `.env.example` model-selection template for launching the Python backend and Node Web UI together.
- Added a copy button for translated output in the Node.js Web UI.
- Fixed server-mode translation requests to use Gradio 6's `/gradio_api/run/translate` endpoint instead of the removed `/api/translate` path.
- Documented the Node.js Web UI startup flow and environment variables in both Japanese and English READMEs.
