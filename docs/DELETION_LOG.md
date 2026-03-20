# Code Deletion Log

## [2026-03-20] Refactor Session

### Unused Dependencies Removed
- なし

### Unused Files Deleted
- なし

### Duplicate Code Consolidated
- `src/cat_translate_cli/cli.py` と `src/cat_translate_cli/translator.py` に重複していた `max_tokens` の既定値を `DEFAULT_MAX_TOKENS` に集約
- Reason: 既定値の不一致を防ぐため

### Unused Exports Removed
- なし

### Kept After Review
- `src/cat_translate_cli/translator.py` の `import llama_cpp`
- Reason: `llama_cpp.llama_cpp.llama_log_set(...)` の呼び出しに必要
- `src/cat_translate_cli/translator.py` の `_LLAMA_LOG_CALLBACK`
- Reason: `ctypes` コールバックがガベージコレクションで解放されるのを防ぐため

### Impact
- Files deleted: 0
- Dependencies removed: 0
- Lines of code removed: 少量
- Bundle size reduction: なし

### Testing
- `uv run ruff check . --select F401,F841,RUF100`
- `uv run vulture src --min-confidence 80`
- `uv run deptry .`
- `uv run mypy src --warn-unreachable`
- `uv run cat-translate --help`
