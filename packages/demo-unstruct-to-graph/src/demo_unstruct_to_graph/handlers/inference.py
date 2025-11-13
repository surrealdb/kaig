import logging

from pydantic import JsonValue
from surrealdb import RecordID

from demo_unstruct_to_graph.definitions import Chunk, EdgeTypes, Tables
from kaig.db import DB

logger = logging.getLogger(__name__)


def inferrence_handler(db: DB, chunk_rec_id: RecordID) -> None:
    logger.info("Starting inference...")

    if not db.llm:
        logger.warning("No LLM configured, skipping inference")
        return

    chunk = db.query_one(
        "SELECT * FROM ONLY $record",
        {"record": chunk_rec_id},
        Chunk,
    )
    if chunk is None:
        raise ValueError(f"Chunk not found {chunk_rec_id}")

    logger.info(f"Inferring chunk: {chunk_rec_id}")
    concepts = db.llm.infer_concepts(chunk.content)
    for concept in concepts:
        concept_id = RecordID(Tables.concept.value, concept)
        _ = db.query_one(
            "UPSERT ONLY $record",
            {"record": concept_id},
            dict[str, JsonValue],
        )
        db.relate(
            chunk.id,
            EdgeTypes.MENTIONS_CONCEPT.value.name,
            concept_id,
        )

    logger.info("Finished inference!")
