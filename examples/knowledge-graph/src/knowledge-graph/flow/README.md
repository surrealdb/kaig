# Flow

This package provides a small orchestrator to run lightweight, database-backed
flows on SurrealDB records. It exposes an `Executor` that registers flow
handlers, selects eligible records, and prevents repeat processing by requiring
handlers to mark their output field.

## Core ideas
- **Flows are declarative.** Use `@executor.flow(table, stamp, dependencies,
  priority)` to describe which table to watch, which field signals completion,
  required dependencies, and optional priority ordering. Flow definitions are
  stored in the `flow` table for observability.
- **Handlers do the work.** Decorated functions receive a record dictionary and
  should perform side effects (e.g., creating related rows) and then update the
  configured output field so the record is not reprocessed.
- **Execution loops are flexible.** Call `execute_flows_once()` to process any
  ready records one time, or `await executor.run()` to keep polling with
  exponential backoff until `executor.stop()` is called.

## Example
```python
from demo_unstruct_to_graph import flow
from kaig.db import DB

db = DB("mem://", "root", "root", "kaig", "demo")
executor = flow.Executor(db)

@executor.flow(table="document", stamp="chunked", dependencies=["text"])
def chunk(record: flow.Record):
    _ = db.sync_conn.query(
        "CREATE chunk SET text = $text, document = $document",
        {"text": record["text"], "document": record["id"]},
    )

    # set output field so it's not reprocessed again
    _ = db.sync_conn.query("UPDATE $rec SET chunked = true", {"rec": record["id"]})

results = executor.execute_flows_once()
# results => {"chunk": processed_count}
```
See `flow/tests/flow_test.py` for a complete chained example that first chunks
new documents and then enriches the resulting chunks.
