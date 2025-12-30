import logging

import logfire

from demo_unstruct_to_graph.definitions import Chunk
from kaig.db import DB

logger = logging.getLogger(__name__)


def summarize_handler(db: DB, chunk: Chunk, force: bool = False) -> None:
    if not db.llm:
        logger.warning("No LLM configured, skipping inference")
        return
    with logfire.span("Summarize {chunk=}", chunk=chunk.id):
        # skip if summary already exists and not force
        if chunk.summary is not None and not force:
            logger.info(f"Summary already exists {chunk.id}")
            return

        summary = db.llm.summarize(chunk.content)
        _ = db.sync_conn.patch(
            chunk.id, [{"op": "replace", "path": "/summary", "value": summary}]
        )
