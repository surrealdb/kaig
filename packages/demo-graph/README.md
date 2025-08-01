---
title: Let's use Graph RAG to organize my things and bookmarks
sub_title: LLM, Vector Search, Graph Queries
author: Martin Schaer <martin.schaer@surrealdb.com>
---

How to run
===

Requirements: [uv](https://docs.astral.sh/uv/), [just](https://just.systems/man/en/)

- start surrealdb: `just db`

# Bookmarks

First you need to export your bookmarks from Firefox to a JSON file.

Ingestion:

```sh
just ingest-bookmarks data/firefox-bookmarks.json
```

Querying:

```sh
# usage: just query-bookmark QUERY
just query-bookmark "karting uk"
```

# Things:

Ingestion:

```sh
# usage: just ingest-things-yaml FILE
just ingest-things-yaml data/things.yaml
```
Querying:

```sh
# usage: just query-thing DB QUERY
just query-thing things-yaml "keyboard"
 ```

<!-- end_slide -->

Queries
===

```surql
SELECT *,<-in_category<-? FROM category;
--
SELECT *, <-has_tag<-? FROM tag;
--
SELECT *,<->? FROM container;
--
SELECT *,->?->? FROM document;
--
SELECT *,
    @.{1}(->stored_in->?) AS cont1,
    @.{2}(->stored_in->?) AS cont2,
    @.{3}(->stored_in->?) AS cont3,
    @.{4}(->stored_in->?) AS cont4,
    @.{5}(->stored_in->?) AS cont5
FROM document;
```

<!-- end_slide -->

Inference score
===

Useful for prompt engineering.

```surql
SELECT score, count(id) FROM analytics GROUP BY score;

LET $bad = SELECT VALUE count FROM ONLY (
    SELECT score, count(id) FROM analytics WHERE score == 0 GROUP BY score
) LIMIT 1;
LET $good = SELECT VALUE count FROM only (
    SELECT score, count(id) FROM analytics WHERE score == 1 GROUP BY score
) LIMIT 1;

RETURN type::float($good||0) / type::float(($bad||0) + ($good||0));
```

<!-- end_slide -->
