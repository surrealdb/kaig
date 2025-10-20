## Run:

```bash
uv run src/demo_unstruct_to_graph/conversion/pdf.py file_name.pdf
```

## SurrealQL queries:

**Visualise the graph:**

```surql
SELECT *,
    ->MENTIONS_CONCEPT->concept as concepts,
    ->CHUNK_FROM_PAGE->page as pages,
    ->CHUNK_FROM_PAGE->page->PAGE_FROM_DOC->document as docs
FROM chunk;
```
