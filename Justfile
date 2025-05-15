mod demo-vanilla './packages/demo-vanilla'
mod demo-langchain './packages/demo-langchain'

default:
    @just --list

format:
    uv run ruff format

lint:
    uv run ruff check
