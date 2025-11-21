## Run:

### DB:

```bash
surreal start -u root -p root rocksdb:database
```

or `just demo-u2g-db` from the repo base directory.

### Server and worker

```bash
OLLAMA_LOG_LEVEL=WARN uv run -- fastapi run packages/demo-unstruct-to-graph/src/demo_unstruct_to_graph/__init__.py --port 8080
```

or `just demo-u2g` from the repo base directory.

## SurrealQL queries:

**Visualise the graph:**

```surql
SELECT *,
    ->MENTIONS_CONCEPT->concept as concepts,
    ->CHUNK_FROM_DOC->document as docs,
    ->SUMMARIZED_BY->summary as summaries
FROM chunk;
```
