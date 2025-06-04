mod demo-vanilla './packages/demo-vanilla'

default:
    @just --list

format:
    uv run ruff format

lint:
    -time uv run ruff check
    -time uv run pyright src/ packages/
    -time uv run ty check
