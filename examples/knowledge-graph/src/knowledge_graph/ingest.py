import logging
import os

from pydantic import TypeAdapter

from kaig.definitions import OriginalDocument
from knowledge_graph import flow
from knowledge_graph.ingestion import markdown

OriginalDocumentTA = TypeAdapter(OriginalDocument)

logger = logging.getLogger(__name__)

db_ns = os.environ.get("SURREALDB_NAMESPACE", "test")
db_name = os.environ.get("SURREALDB_DATABASE", "test")


async def main() -> None:
    db = init_kaig(ns=db_ns, db=db_name)
    db.apply_schemas()
    exe: flow.Executor = flow.Executor(db)
    print("Starting ingestion loop...")
    await markdown.ingestion_loop(exe)


if __name__ == "__main__":
    import asyncio

    from knowledge_graph.db import init_kaig

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
