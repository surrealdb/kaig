## Run:

```bash
uv run -- fastapi run packages/demo-unstruct-to-graph/src/demo_unstruct_to_graph/__init__.py --port 8080
```

## SurrealQL queries:

**Visualise the graph:**

```surql
SELECT *,
    ->MENTIONS_CONCEPT->concept as concepts,
    ->CHUNK_FROM_DOC->document as docs
FROM chunk;
```
