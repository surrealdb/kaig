## Run:

### DB:

```bash
surreal start -u root -p root rocksdb:dbs/knowledge-graph
```

or `just knowledge-graph-db` from the repo base directory.

### Server and worker

```bash
uv run --env-file .env -- fastapi run examples/knowledge-graph/src/knowledge-graph/server.py --port 8080
```

or `just knowledge-graph` from the repo base directory.

## SurrealQL queries:

**Visualise the graph:**

```surql
SELECT *,
    ->MENTIONS_CONCEPT->concept as concepts,
    ->CHUNK_FROM_DOC->document as docs,
    ->SUMMARIZED_BY->summary as summaries
FROM chunk;
```
