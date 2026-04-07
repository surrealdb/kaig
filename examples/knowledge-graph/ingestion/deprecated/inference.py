import logging
from textwrap import dedent

import logfire
from db.definitions import Chunk
from surrealdb import RecordID

from kaig.db import DB
from kaig.definitions import BaseDocument

logger = logging.getLogger(__name__)


class Concept(BaseDocument):
    id: RecordID


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
            concept_id = RecordID("concept", concept)
            _ = db.embed_and_insert(
                Concept(content=concept, id=concept_id),
                table="concept",
                id=concept,
            )
            db.relate(
                chunk.id,
                "MENTIONS_CONCEPT",
                concept_id,
            )

        logger.info("Finished inference!")
        return concepts
