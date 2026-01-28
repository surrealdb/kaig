from .db import init_db
from .definitions import Chunk


def search_chunks(query: str, db_name: str) -> None:
    db = init_db(False, db_name)
    res, _time = db.vector_search_from_text(Chunk, query, table="chunk", k=10)
    if res:
        for x, score in res:
            print(
                f"\nscore: {score * 100:.2f}%, id: {x.id.id}\n{x.content[:80]}"
            )


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python search.py <db_name> <query>")
        sys.exit(1)

    db_name = sys.argv[1]
    query = sys.argv[2]
    print(f"query: {query}")
    search_chunks(query, db_name)
