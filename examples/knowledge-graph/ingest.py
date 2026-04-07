import logging
import os

from db import init_kaig
from ingestion import ingestion_loop
from pydantic import TypeAdapter

from kaig import flow
from kaig.definitions import OriginalDocument

OriginalDocumentTA = TypeAdapter(OriginalDocument)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

db_url = os.environ.get("SURREALDB_URL", "ws://localhost:8000")
db_ns = os.environ.get("SURREALDB_NAMESPACE", "test")
db_name = os.environ.get("SURREALDB_DATABASE", "test")


async def main() -> None:
    db = init_kaig(url=db_url, ns=db_ns, db=db_name)
    db.apply_schemas()
    exe: flow.Executor = flow.Executor(db)
    print("Starting ingestion loop...")
    await ingestion_loop(exe)


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
