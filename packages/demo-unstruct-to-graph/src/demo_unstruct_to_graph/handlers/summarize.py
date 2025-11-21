import logging

from pydantic import JsonValue
from surrealdb import RecordID

from demo_unstruct_to_graph.definitions import Chunk, EdgeTypes, Tables
from kaig.db import DB

logger = logging.getLogger(__name__)


def summarize_handler(
    db: DB, chunk_rec_id: RecordID, force: bool = False
) -> None:
    logger.info("Starting inference...")

    if not db.llm:
        logger.warning("No LLM configured, skipping inference")
        return

    chunk = db.query_one(
        "SELECT * FROM ONLY $record", {"record": chunk_rec_id}, Chunk
    )
    if chunk is None:
        raise ValueError(f"Chunk not found {chunk_rec_id}")

    summary_id = RecordID(
        Tables.summary.value,
        chunk.id.id,  # pyright: ignore[reportAny]
    )

    if db.exists(summary_id) and not force:
        logger.info(f"Summary already exists {summary_id}")
    else:
        logger.info(f"Summarizing chunk: {chunk_rec_id}")
        summary = db.llm.summarize(chunk.content)
        _ = db.query_one(
            "UPSERT ONLY $record SET content = $content",
            {"record": summary_id, "content": summary},
            dict[str, JsonValue],
        )

    db.relate(
        chunk.id,
        EdgeTypes.SUMMARIZED_BY.value.name,
        summary_id,
    )

    logger.info("Finished inference!")
