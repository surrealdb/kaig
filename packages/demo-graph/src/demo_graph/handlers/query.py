from demo_graph.models import Thing

from kai_graphora.db import DB
from kai_graphora.llm import LLM


def query_handler(db: DB, llm: LLM, query: str) -> None:
    print("Querying...")
    res = db.vector_search(
        query, llm.gen_embedding_from_desc(query), table="document"
    )

    print("\nThings:")
    for x in res:
        print(f"•{x['dist']:.0%}: {x.get('name')}", end="")
        things_with_containers = db.recursive_graph_query(Thing, x["id"], "stored_in")
        print(". Find it in: ", end="")
        for x in things_with_containers:
            print(" > ".join([b.id for b in x.buckets]))

    res = db.vector_search(
        query, llm.gen_embedding_from_desc(query), table="tag"
    )

    print("\nTags:")
    for x in res:
        print(f"•{x['dist']:.0%}: {x.get('name')}")

    res = db.vector_search(
        query, llm.gen_embedding_from_desc(query), table="category"
    )

    print("\nCategories:")
    for x in res:
        print(f"•{x['dist']:.0%}: {x.get('name')}")
