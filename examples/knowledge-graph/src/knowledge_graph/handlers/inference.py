import logging
from textwrap import dedent

import logfire
from surrealdb import RecordID

from kaig.db import DB

from ..definitions import Chunk, Concept, EdgeTypes, Tables

logger = logging.getLogger(__name__)


def inferrence_handler(db: DB, chunk: Chunk) -> list[str]:
    if not db.llm:
        logger.warning("No LLM configured, skipping inference")
        return []
    with logfire.span("Extract concepts {chunk=}", chunk=chunk.id):
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
        return concepts
