# AGENTS.md

## Setup commands

- Activate virtual environment: `. .venv/bin/activate`
- Install dependencies: `uv sync --all-packages`
- Run diagnostics: `uv run basedpyright src/ packages/ --level error`
- Format code: `uv run ruff format && uv run ruff check --fix --select I`
