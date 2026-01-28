mod demo-graph './examples/demo-graph'
mod demo-ingest-throttled './examples/demo-ingest-throttled'

default:
    @just --list

format:
    uv run ruff check --fix --select I
    uv run ruff format

lint:
    -time uv run ruff check
    -time uv run basedpyright src/
    -time uv run basedpyright -p examples/demo-graph
    -time uv run basedpyright -p examples/demo-simple
    -time uv run basedpyright -p examples/knowledge-graph
    # -time uv run ty check

# DB for knowledge-graph example
knowledge-graph-db:
    surreal start -u root -p root rocksdb:databases/knowledge-graph

# Run knowledge-graph example ingestion server
knowledge-graph DB:
    DB_NAME={{DB}} uv run --env-file .env -- fastapi run examples/knowledge-graph/src/knowledge_graph/server.py --port 8080

# Run knowledge-graph example agent chat UI
knowledge-graph-agent DB:
    DB_NAME={{DB}} uv run --env-file .env uvicorn knowledge_graph.agent:app --host 127.0.0.1 --port 7932

# Alias for knowledge-graph-db
kg-db:
    @just knowledge-graph-db

# Alias for knowledge-graph
kg DB:
    @just knowledge-graph {{DB}}

# Alias for knowledge-graph-agent
kg-agent DB:
    @just knowledge-graph-agent {{DB}}
