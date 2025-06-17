from kai_graphora.db import DB
from kai_graphora.llm import LLM


def query_handler(db: DB, llm: LLM, query: str) -> None:
    print("Querying...")
    res = db.vector_search(query, llm.gen_embedding_from_desc(query), table="document")
    for x in res:
        print(f"{x.get("dist")}: {x.get("name")}")
