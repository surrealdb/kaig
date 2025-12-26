> [!IMPORTANT]
> This repo is experimental. Use it as an example to implement your own solutions, or clone and install it as a local dependency.

<p align="center">
  <a href="https://github.com/martinschaer/kaig">
    <img loading="lazy" alt="Kai G" src="./docs/assets/kaig-pic.png" width="100%" />
  </a>
</p>

# Kai G

> /ˈkaɪ ˈdʒiː/ – Kai rhymes with sky, and G like the letter G.

Hi! Let me handle your DB needs for your AI project. If you need **vector search**,
or **graph queries**, I've got you covered. I use [SurrealDB](https://surrealdb.com)
under the hood, which is a multi-model DB that greatly simplifies your architecture.

## Getting started

```python
# Set up your vector indexes and graph relations
db = DB(
    "ws://localhost:8000/rpc",
    username,
    password,
    ns,
    db,
    Embedder("all-minilm:22m", "F32")
    LLM(),
    vector_tables=[
        VectorTableDefinition("document", "HNSW", "COSINE"),
        VectorTableDefinition("keyword", "HNSW", "COSINE"),
        VectorTableDefinition("category", "HNSW", "COSINE"),
    ],
    graph_relations=[
        Relation("has_keyword", "document", "keyword"),
        Relation("in_category", "document", "category"),
        Relation("stored_in", "document|container", "container"),
    ],
)
db.init_db()
```

This will generate a schema similar to this (which you can see in the Designer
tab of [Surrealist](https://surrealdb.com/surrealist)):

![db schema](./docs/assets/schema.png)

## Ingesting

This sample code inserts documents in the vector store, and creates a graph with
documents related to keywords.

```python
keywords: set[str] = set()
doc_to_keywords: dict[str, set[str]] = {}

for doc in documents:
    # This function generated the embeddings for the document
    db.embed_and_insert(doc)

    # Collect keywords
    keywords.update(doc.keywords)

    # Link documents with keywords
    if doc.id not in doc_to_keywords:
        doc_to_keywords[doc.id] = set()
    for keyword in doc.keywords:
        doc_to_keywords[doc.id].add(keyword)

# This function generates embeddings for the keywords (destination nodes)
db.add_graph_nodes_with_embeddings(
    src_table: "document",
    dest_table: "keyword",
    destinations: keywords,
    edge_name: "has_keyword",
    relations: doc_to_keywords
)
```

## Querying

```python
res, time = db.vector_search_from_text(
    Document,  # results are validated-against- and cast-to- this type
    "Dalinar Kholin",
    table="document",
    k=5,
    score_threshold=0.5,
    effort=40,
)
for x, score in res:
    print(f"• {score:.0%}: {x.content}")
print(f"Query took {time}ms")
```

## APIs

### kaig.db.DB

**Setup functions** | **Description**
-|-
init_db | initialize DB schema/indexes (vector tables, graph relations, analytics/docs tables)
clear | drop tables/indexes created/used by this instance
original_docs_table | name of the original documents table
async_conn | get an authenticated async connection (lazy)
sync_conn | get an authenticated sync connection (lazy)

**Data functions** | **Description**
-|-
execute | run a SurrealQL query loaded from a `.surql` file (sync)
async_execute | run a SurrealQL query loaded from a `.surql` file (async)
query | query a list of records and validate them as the expected type
query_one | query a single record and validate it as the expected type
count | count how many records match a query (optionally grouped)
exists | check if a record exists by record id
insert_analytics_data | insert a record in the analytics table
safe_insert_error | insert a record in the errors table (async, best-effort)
error_exists | check if an error record exists for a given id (async)
store_original_document | store an original file (as bytes) and dedupe by hash
store_original_document_from_bytes | store an original file from bytes and dedupe by hash
get_document | get a document/chunk by id (async)
list_documents | list documents/chunks with pagination (async)
async_insert_document | insert a document/chunk asynchronously
insert_document | insert a document/chunk synchronously
embed_and_insert | generate an embedding (if needed) and insert the document/chunk
vector_search_from_text | embed query text and run a vector search
vector_search | run a vector search with a provided embedding
async_vector_search | run a vector search with a provided embedding (async)
relate | create graph edges between records
add_graph_nodes | upsert destination nodes and relate them
add_graph_nodes_with_embeddings | embed + upsert destination nodes and relate them
recursive_graph_query | fetch children recursively up to N levels
graph_query_inward | fetch parent nodes (optionally using an embedding for ranking)
graph_siblings | fetch nodes that share the same parent

### kaig.llm.LLM

**Function** | **Description**
-|-
gen_name_from_desc | generate a name from a description
gen_answer | generate an answer from a question and a context
infer_attributes | use a pydantic BaseModel to have the LLM infer the attributes

## Next steps

- Take a look at the [packages](https://github.com/martinschaer/kaig/tree/main/packages) folder.
- Get familiar with SurrealQL:
  - [SurrealQL intro queries](./docs/surql-intro.surql)
  - [Official SurrealQL docs](https://surrealdb.com/docs/surrealql)

## Visualizing the graph

Using [Surrealist](https://surrealdb.com/surrealist)

Example query from all `document`s connected by any edge (`?`) to any other nodes (`?`):

```sql
SELECT *, ->?->? FROM document;
```

![graph visualization](./docs/assets/surrealist-graph.png)
