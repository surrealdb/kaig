mod demo-graph './packages/demo-graph'
mod demo-ingest-throttled './packages/demo-ingest-throttled'

default:
    @just --list

format:
    uv run ruff check --fix --select I
    uv run ruff format

lint:
    -time uv run ruff check
    -time uv run pyright src/ packages/
    -time uv run ty check
