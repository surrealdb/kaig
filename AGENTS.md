# AGENTS
Scope: entire repository.
Python 3.12 with uv-managed .venv.
Install deps: `uv sync --all-packages` (or `uv sync` after activating env).
Format imports: `uv run ruff check --fix --select I`.
Format code: `uv run ruff format` (line length 80, indent 4).
Lint: `uv run ruff check`.
Type check: `uv run basedpyright src/ packages/ --level error`.
Package-specific type checks: `uv run basedpyright -p packages/<pkg>`.
Tests all: `uv run pytest`.
Single test/file: `uv run pytest src/kaig/tests/test_foo.py -k name`.
Prefer isolated, deterministic pytest tests; avoid external service reliance.
Imports: absolute over relative; no wildcards; stdlib/third-party/local grouped (ruff sorts).
Typing: use precise annotations and `collections.abc` generics; avoid `Any`; prefer `| None` for optionals.
Naming: snake_case for vars/functions, PascalCase for classes, UPPER_SNAKE for constants.
Error handling: raise clear exceptions, avoid silent pass; log via `logfire` when useful.
Formatting: favor f-strings, double quotes, trailing commas for multi-line.
Data models: use Pydantic/BaseModel where structured data exchanged; validate inputs.
Secrets/config: load from env vars (e.g., `OPENAI_API_KEY`); never commit keys.
No Cursor or Copilot rules present beyond this file.
