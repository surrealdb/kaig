# AGENTS
This playbook is for agentic contributors working in this repository.
Follow these rules unless a task explicitly overrides them. Keep edits in ASCII.

## Scope and Environment
- Scope: entire repository (root + `examples/*`).
- Runtime: Python 3.12, uv-managed `.venv` (do not swap toolchains).
- Workspace: uv workspace members include `examples/*` (demo apps and notebooks).
- Platform: macOS; SurrealDB used for examples; keep commands portable.
- No Cursor rules (`.cursor/rules`, `.cursorrules`) or Copilot instructions found.

## Setup and Dependencies
- Create/activate env with uv: `uv sync --all-packages` (or `uv sync` inside the venv).
- If env already present, prefer `uv run ...` to ensure deps resolve via uv.
- Lockfile: `uv.lock` is source of truth; avoid hand-editing.
- Additional sources: `pyproject.toml` pins workspace extras (logfire from Git, surrealfs-py via Git in knowledge-graph example).

## Core Commands (root package `kaig`)
- Format imports: `uv run ruff check --fix --select I`.
- Format code: `uv run ruff format` (80 cols, 4-space indent, double quotes, trailing commas on multi-line).
- Lint: `uv run ruff check` (keep clean; prefer fixing warnings rather than ignoring).
- Type check all: `uv run basedpyright src/ examples/ --level error`.
- Package-specific type check: `uv run basedpyright -p examples/<pkg>` (e.g., `examples/knowledge-graph`).
- Tests (all): `uv run pytest`.
- Tests (single file): `uv run pytest src/kaig/tests/test_db.py` (adjust path).
- Tests (single test): `uv run pytest src/kaig/tests/test_db.py -k test_name`.
- Keep tests deterministic; avoid hitting external services. Mock SurrealDB/LLM when possible.

## Justfile Shortcuts (run with `just <recipe>`)
- `format`: runs import sort then formatter.
- `lint`: ruff check + basedpyright for root and selected examples.
- `knowledge-graph-db` / `kg-db`: start SurrealDB locally for the knowledge-graph example (`surreal start -u root -p root rocksdb:databases/knowledge-graph`).
- `knowledge-graph DB` / `kg DB`: run FastAPI ingestion server with `DB_NAME` env, e.g. `just kg test_db` (wraps `uv run --env-file .env -- fastapi run examples/knowledge-graph/src/knowledge_graph/server.py --port 8080`).
- `knowledge-graph-agent DB` / `kg-agent DB`: start chat agent UI, e.g. `just kg-agent test_db` (wraps `uv run --env-file .env uvicorn knowledge_graph.agent:app --host 127.0.0.1 --port 7932`).

## Repository Layout (anchors for navigation)
- `src/kaig`: core library (DB, embeddings, LLM utilities, definitions, tests under `src/kaig/tests`).
- `docs/`: assets and SurrealQL references.
- `examples/knowledge-graph`: ingestion + chat example (FastAPI + data-flow executor + PydanticAI agent).
- `examples/demo-graph`, `examples/demo-simple`, `examples/demo-ingest-throttled`, `examples/notebooks`: other workspace members; follow their local pyproject settings.
- `Justfile`: authoritative task runner; prefer recipes over custom scripts when available.

## Knowledge Graph Example Quickstart (from repo root)
- Start DB: `just knowledge-graph-db` (or `surreal start -u root -p root rocksdb:databases/knowledge-graph`).
- Run server + ingestion worker: `DB_NAME=test_db just knowledge-graph test_db` or the underlying uv command from README.
- Run chat agent: `DB_NAME=test_db just knowledge-graph-agent test_db`.
- SurrealQL helper queries live in `examples/knowledge-graph/surql/` (schema + retrieval).
- Flow-based ingestion uses stamp fields; updating handler code changes hashes—watch flow tables to gauge progress.
- To inspect flow status, run the SurrealQL snippet from `examples/knowledge-graph/README.md` under a Surreal client.
- Local tmp directories (`examples/knowledge-graph/tmp`, root `tmp/`) may hold artifacts; do not commit transient outputs.

## Style and Implementation Guidelines
- Imports: absolute only; no wildcards; group stdlib/third-party/local (ruff handles ordering).
- Prefer `from collections.abc import Iterable, Callable, ...` over `typing.List` etc.
- Typing: be explicit; avoid `Any`; use `| None` for optional; mark callables precisely; consider Protocols instead of duck-typing comments.
- Public interfaces: annotate return types; keep function signatures narrow and clear.
- Dataclasses vs Pydantic: favor Pydantic `BaseModel` for structured data exchange and validation; keep validators minimal and explicit.
- Error handling: raise specific exceptions with actionable messages; avoid bare `except`; never silently `pass`; when useful, log via `logfire`. Re-raise with `from` to preserve context.
- Logging/tracing: prefer structured logs; avoid print; ensure secrets are redacted.
- Formatting: f-strings; double quotes; trailing commas on multiline collections/calls; keep lines ≤ 80 chars.
- Naming: snake_case for variables/functions; PascalCase for classes; UPPER_SNAKE for constants; module filenames snake_case.
- Mutability: prefer immutable data where practical; copy before mutating shared inputs.
- File paths: use `pathlib.Path`; avoid hard-coded relative string paths.
- Timeouts/retries: set explicit timeouts for network/DB calls; avoid unbounded loops.
- Async: when adding async code, use `asyncio` best practices; avoid blocking calls; close sessions/clients.
- Database (SurrealDB): parameterize NS/DB/user/pass via env; never hard-code credentials; keep schema changes in `.surql` files.
- Vector/LLM: prefer dependency injection for models/embedders to keep tests hermetic; mock external calls in tests.
- CLI/servers: guard entrypoints with `if __name__ == "__main__"` when adding scripts; ensure uvicorn/fastapi commands reference module paths (not local file assumptions).
- Documentation: update README snippets when changing APIs; keep docstrings concise and informative.
- Comments: add only when behavior is non-obvious; keep them up to date.

## Testing Guidance
- Add tests under `src/kaig/tests` or relevant example packages; name files `test_*.py`.
- Structure tests for determinism; seed randomness; isolate filesystem writes under `tmp/` or pytest `tmp_path`.
- Avoid networked dependencies; mock SurrealDB/LLM/embedding calls.
- Use pytest markers sparingly; default to unit-style tests; no skipped tests unless necessary.
- When debugging flows, prefer targeted tests with small fixtures rather than full DB spins.

## Git and Workflow Notes
- Do not rewrite existing user changes. Avoid destructive git commands (no hard reset/checkout).
- Only commit when explicitly asked. Keep branches clean; respect repo commit style by inspecting `git log` if needed.
- Secrets: never commit `.env`, credentials, tokens, or SurrealDB passwords. Use env vars and `.env` locally only.

## Observability and Telemetry
- logfire is available (via dev deps). If adding logs, use structured logging and keep PII out.
- Prefer surfacing operational metrics through structured events rather than ad-hoc prints.

## SurrealQL Artifacts
- Surreal queries live in `docs/surql-intro.surql` and `examples/knowledge-graph/surql/*`. Keep queries in `.surql` files and load them via helpers (`DB.execute` / `async_execute`).
- When modifying schema or retrieval queries, keep them idempotent and documented in README sections.

## Configuration Defaults
- Knowledge-graph server requires `DB_NAME` env; it defaults Surreal connection to `ws://localhost:8000/rpc`, user `root`, pass `root`, namespace `kaig`.
- LLM defaults (knowledge-graph): provider `openai`, model `gpt-5-mini-2025-08-07`, temperature 1; embedder uses OpenAI `text-embedding-3-small` with vector type `F32`.
- Supply API keys via env (e.g., `OPENAI_API_KEY`); do not hard-code credentials. Use `.env` locally and keep it untracked.
- Keep Surreal schema definitions in `.surql` files; re-run init if tables/edges change.
- Avoid clearing DB automatically unless you know it is safe (`db.clear()` is commented out by default).

## Knowledge-Graph Flow Notes
- Flow executor registers handlers via `@exe.flow(...)` and writes handler hashes into stamp fields to avoid re-processing.
- Current flows: `chunk` operates on `document` rows lacking a `chunked` stamp; `infer_concepts` operates on `chunk` rows lacking `concepts_inferred`.
- Flow eligibility: stamp is `NONE` and dependencies satisfied; this makes runs restart-safe and incremental.
- When updating a flow handler, expect hash changes; use the flow status SurrealQL snippet (README) to see processed vs pending records.
- Background ingestion loop starts with FastAPI server startup (`ingestion_loop` task) and stops gracefully on shutdown.
- Upload route (`/upload`) schedules ingestion via background task; keep handlers async-safe and best-effort idempotent.

## Data and Assets
- Images and docs live under `docs/assets/`; keep large binaries out of git unless essential.
- Temp artifacts: `tmp/`, `examples/knowledge-graph/tmp`, `databases/`, `uploads/` should stay untracked; clean them before sharing branches.
- `.surql` files are canonical for DB schema and queries—do not duplicate queries inline unless necessary for tests.

## Packaging and Imports
- Root `pyproject.toml` defines workspace members; use uv workspace semantics rather than ad-hoc `pip install -e .`.
- Dev dependencies live under `[dependency-groups].dev`; run `uv sync --all-packages` to pull workspace extras.
- Example packages (e.g., `knowledge-graph`) depend on the root package via workspace source; avoid circular imports across packages.

## Review Checklist
- Lint + format + type-check before sharing changes: run `just format` then `just lint` or the underlying uv commands.
- Confirm tests relevant to your changes pass (single file/test commands above).
- Validate knowledge-graph flows still stamp correctly after handler edits (check flow status query if unsure).
- Ensure new endpoints/CLI entrypoints include parameter validation and do not hard-code secrets or ports.
- Update documentation (README/AGENTS/SurrealQL files) when adjusting APIs, env vars, or schema.

## Safety and Cleanup
- Clean temp outputs before PRs; ignore transient folders (`tmp/`, `uploads/`, `databases/`).
- If running servers, stop them after tests to avoid port conflicts (8080 for FastAPI, 7932 for agent UI by default).
- When adding new commands, prefer `just` recipes or document the uv invocation clearly.

## Quick Reference (copy/paste)
- Install deps: `uv sync --all-packages`
- Format imports: `uv run ruff check --fix --select I`
- Format code: `uv run ruff format`
- Lint: `uv run ruff check`
- Type check (all): `uv run basedpyright src/ examples/ --level error`
- Type check (pkg): `uv run basedpyright -p examples/knowledge-graph`
- Tests (all): `uv run pytest`
- Tests (file): `uv run pytest src/kaig/tests/test_db.py`
- Tests (single): `uv run pytest src/kaig/tests/test_db.py -k test_name`
- Start KG DB: `just kg-db`
- Run KG server: `DB_NAME=test_db just kg test_db`
- Run KG agent: `DB_NAME=test_db just kg-agent test_db`
