import logging

import logfire
from surrealdb import RecordID

from demo_unstruct_to_graph.definitions import Chunk
from kaig.db import DB

logger = logging.getLogger(__name__)


def summarize_handler(
    db: DB, chunk_rec_id: RecordID, force: bool = False
) -> None:
    with logfire.span("Summarize {chunk_rec_id=}", chunk_rec_id=chunk_rec_id):
        logger.info("Starting inference...")

        if not db.llm:
            logger.warning("No LLM configured, skipping inference")
            return

        chunk = db.query_one(
            "SELECT * FROM ONLY $record", {"record": chunk_rec_id}, Chunk
        )
        if chunk is None:
            raise ValueError(f"Chunk not found {chunk_rec_id}")

        # skip if summary already exists and not force
        if chunk.summary is not None and not force:
            logger.info(f"Summary already exists {chunk.id}")
            return

        summary = db.llm.summarize(chunk.content)
        _ = db.sync_conn.patch(
            chunk.id, [{"op": "replace", "path": "/summary", "value": summary}]
        )

        logger.info("Finished inference!")
