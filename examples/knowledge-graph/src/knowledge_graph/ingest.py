import logging

from pydantic import TypeAdapter

from kaig.definitions import OriginalDocument
from knowledge_graph import flow
from knowledge_graph.ingestion import markdown

OriginalDocumentTA = TypeAdapter(OriginalDocument)

logger = logging.getLogger(__name__)


async def main() -> None:
    db = init_db(True, "surrealdb")
    exe: flow.Executor = flow.Executor(db)
    print("Starting ingestion loop...")
    await markdown.ingestion_loop(exe)


if __name__ == "__main__":
    import asyncio

    from knowledge_graph.db import init_db

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
