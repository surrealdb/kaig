mod demo-vanilla './packages/demo-vanilla'
mod demo-langchain './packages/demo-langchain'

default:
    @just --list

format:
    uv run ruff format

lint:
    -time uv run ruff check
    -time uv run pyright src/ packages/
    -time uvx ty check
