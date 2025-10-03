from demo_unstruct_to_graph import Chunk, init_db


def search_chunks(query: str) -> None:
    db = init_db(False)
    res, _time = db.vector_search_from_text(Chunk, query, table="chunk", k=10)
    if res:
        for x, score in res:
            print(
                f"\nscore: {score * 100:.2f}%, id: {x.id.id}\n{x.content[:80]}"
            )


if __name__ == "__main__":
    import sys

    query = sys.argv[1]
    print(f"query: {query}")
    search_chunks(query)
