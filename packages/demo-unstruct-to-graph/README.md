## Run:

DB:

```bash
surreal start -u root -p root --allow-net=127.0.0.1 rocksdb:database
```

```bash
OLLAMA_LOG_LEVEL=WARN uv run -- fastapi run packages/demo-unstruct-to-graph/src/demo_unstruct_to_graph/__init__.py --port 8080
```

## SurrealQL queries:

**Visualise the graph:**

```surql
SELECT *,
    ->MENTIONS_CONCEPT->concept as concepts,
    ->CHUNK_FROM_DOC->document as docs
FROM chunk;
```
