# Knowledge Graph Example

This example builds a simple **knowledge graph** on top of **SurrealDB** from
uploaded documents, using a **data-flow pattern** to drive ingestion.

At a high level:

1. You upload a document to the DB using `kaig-app` web UI.
2. The server stores it in SurrealDB as a `file` record.
3. A background ingestion worker runs *flows* that:
   - chunk documents into embedded `chunk` records
   - ...
4. A separate chat agent can retrieve relevant chunks (vector + graph context)
   and answer using the ingested documents.

## Run:

See [kaig-app/README.md](../../kaig-app/README.md).

### Chat agent

```bash
DB_NAME=test_db uv run --env-file .env uvicorn knowledge_graph.agent:app --host 127.0.0.1 --port 7932
```

or `just knowledge-graph-agent test_db` from the repo base directory.

## SurrealQL queries:

**Visualise the graph:**

```surql
SELECT *,
    ->MENTIONS_CONCEPT->concept as concepts
FROM chunk;
```

**Flow status**

This will show how many records have been processed by and are pending for each "flow".

```surql
LET $flows = SELECT * FROM flow;

RETURN $flows.fold([], |$a, $flow| {
    LET $b = SELECT
            $flow.id as flow,
            type::field($flow.stamp) as flow_hash,
            count() as count,
            $flow.table as table
        FROM type::table($flow.table)
        GROUP BY flow_hash;
    RETURN $a.concat($b)
});
```

Output example:

```surql
[
	{
		count: 1,
		flow: flow:chunk,
		flow_hash: NONE,
		table: 'document'
	},
	{
		count: 2,
		flow: flow:chunk,
		flow_hash: 'bbb6fe4b55cce1b3c8af0e7713a33d75',
		table: 'document'
	},
	{
		count: 4,
		flow: flow:infer_concepts,
		flow_hash: NONE,
		table: 'chunk'
	},
	{
		count: 27,
		flow: flow:infer_concepts,
		flow_hash: '75f90c71db9aeb2cf6f871ba1f75828c',
		table: 'chunk'
	}
]
```

Different hashes mean the records have been processed by different versions of the flow function. This can happen if the flow function has been updated.
