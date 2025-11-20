import logging

from pydantic import JsonValue
from surrealdb import RecordID

from demo_unstruct_to_graph.definitions import Chunk, EdgeTypes, Tables
from kaig.db import DB

logger = logging.getLogger(__name__)


def summarize_handler(db: DB, chunk_rec_id: RecordID) -> None:
    logger.info("Starting inference...")

    if not db.llm:
        logger.warning("No LLM configured, skipping inference")
        return

    chunk = db.query_one(
        "SELECT * FROM ONLY $record", {"record": chunk_rec_id}, Chunk
    )
    if chunk is None:
        raise ValueError(f"Chunk not found {chunk_rec_id}")

    logger.info(f"Summarizing chunk: {chunk_rec_id}")
    summary = db.llm.summarize(chunk.content)
    summary_id = RecordID(Tables.summary.value, summary)
    _ = db.query_one(
        "UPSERT ONLY $record",
        {"record": summary_id},
        dict[str, JsonValue],
    )
    db.relate(
        chunk.id,
        EdgeTypes.SUMMARIZED_BY.value.name,
        summary_id,
    )

    logger.info("Finished inference!")
