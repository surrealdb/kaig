# kaig-app

## Running

**DB**

```bash
just kaig-app-db
# or
docker run --rm --pull always -p 8000:8000 surrealdb/surrealdb:v3.0.4 start -u root -p root
```

**Worker**

```bash
uv run --env-file .env examples/knowledge-graph/src/knowledge_graph/ingest.py
```

**DB migrations**

After running the worker.

```bash
just kaig-app-migrate
# or
bun run kaig-app/scripts/migrate.ts
```

**App**

```bash
just kaig-app-dev
# or
bun run --cwd kaig-app dev
```

**Agent chat**

```bash
just kaig-app-agent
# or
ENABLE_SURREALFS=true uv run --env-file .env uvicorn knowledge_graph.agent:app --host 127.0.0.1 --port 7932
```
