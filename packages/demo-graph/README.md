---
title: Let's use Graph RAG to organize my things
sub_title: LLM, Vector Search, Graph Queries
author: Martin Schaer <martin.schaer@surrealdb.com>
theme:
  name: surreal
---

How to run it
===

- start surrealdb: `just demo-graph db`
- ingest the data: `just demo-graph demo-bookmarks firefox-bookmarks.json`
- query: `just demo-graph query-bookmark [search term]` e.g. `just demo-graph query-bookmark karting`

Inference score
===

```surql
SELECT score, count(id) FROM analytics GROUP BY score;

LET $bad = SELECT VALUE count FROM ONLY (
    SELECT score, count(id) FROM analytics WHERE score == 0 GROUP BY score
) LIMIT 1;
LET $good = SELECT VALUE count FROM only (
    SELECT score, count(id) FROM analytics WHERE score == 1 GROUP BY score
) LIMIT 1;

RETURN type::float($good) / type::float($bad + $good);
```

<!-- end_slide -->
