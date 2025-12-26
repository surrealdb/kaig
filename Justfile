mod demo-graph './packages/demo-graph'
mod demo-ingest-throttled './packages/demo-ingest-throttled'

default:
    @just --list

format:
    uv run ruff check --fix --select I
    uv run ruff format

lint:
    -time uv run ruff check
    -time uv run basedpyright src/
    -time uv run basedpyright -p packages/demo-graph
    -time uv run basedpyright -p packages/demo-simple
    -time uv run basedpyright -p packages/demo-unstruct-to-graph
    # -time uv run ty check

db:
    surreal start -u root -p root rocksdb:database

demo-unstruct-to-graph:
    uv run --env-file .env -- fastapi run packages/demo-unstruct-to-graph/src/demo_unstruct_to_graph/server.py --port 8080

demo-u2g:
    @just demo-unstruct-to-graph

demo-u2g-db:
    surreal start -u root -p root rocksdb:databases/demo-unstruct-to-graph
