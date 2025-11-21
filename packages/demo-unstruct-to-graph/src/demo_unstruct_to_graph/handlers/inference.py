import logging
from textwrap import dedent

from surrealdb import RecordID

from demo_unstruct_to_graph.definitions import Chunk, Concept, EdgeTypes, Tables
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

    instructions = dedent("""
        - Only return concepts that are: names, places, people, organizations, events, products, services, etc.
        - Do not include symbols or numbers
    """)

    concepts = db.llm.infer_concepts(chunk.content, instructions)
    logger.info(f"Concepts: {concepts}")

    for concept in concepts:
        concept_id = RecordID(Tables.concept.value, concept)
        _ = db.embed_and_insert(
            Concept(content=concept, id=concept_id),
            table=Tables.concept.value,
            id=concept,
        )
        db.relate(
            chunk.id,
            EdgeTypes.MENTIONS_CONCEPT.value.name,
            concept_id,
        )

    logger.info("Finished inference!")
