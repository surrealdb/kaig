mod demo-graph './examples/demo-graph'

# -- Variables

db_version := "v3.0.4"

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
    docker run --rm --pull always -p 8000:8000 -v ./databases:/databases surrealdb/surrealdb:{{ db_version }} start -u root -p root rocksdb:databases/knowledge-graph-v3

# Run knowledge-graph example agent chat UI
knowledge-graph-agent DB:
    SURREALDB_DATABASE={{ DB }} PYTHONPATH=examples/knowledge-graph uv run --env-file .env uvicorn agent:app --host 127.0.0.1 --port 7932

# Alias for knowledge-graph-db
kg-db:
    @just knowledge-graph-db

# Alias for knowledge-graph
kg DB:
    @just knowledge-graph {{ DB }}

# Alias for knowledge-graph-agent
kg-agent DB:
    @just knowledge-graph-agent {{ DB }}

# KaiG app README
kaig-app:
    @glow kaig-app/README.md

# Dev server for kaig-app
kaig-app-dev DB:
    SURREALDB_DATABASE={{ DB }} bun run --cwd kaig-app dev

kaig-app-format:
    bun run --cwd kaig-app format

# Run SurrealDB migrations for kaig-app
kaig-app-migrate DB:
    SURREALDB_DATABASE={{ DB }} bun run kaig-app/scripts/migrate.ts

# Run kaig-app worker
kaig-app-worker DB:
    SURREALDB_DATABASE={{ DB }} uv run --env-file .env examples/knowledge-graph/ingest.py

# Local SurrealDB for kaig-app
kaig-app-db:
    # mkdir -p databases
    [ -d databases ] || mkdir databases
    docker run --rm --pull always -p 8000:8000 --user $(id -u) -v $(pwd)/databases:/databases surrealdb/surrealdb:{{ db_version }} start -u root -p root rocksdb:/databases/kaig-app

# KaiG agent chat UI
kaig-app-agent DB:
    SURREALDB_DATABASE={{ DB }} ENABLE_SURREALFS=true PYTHONPATH=examples/knowledge-graph uv run --env-file .env uvicorn agent:app --host 127.0.0.1 --port 7932
