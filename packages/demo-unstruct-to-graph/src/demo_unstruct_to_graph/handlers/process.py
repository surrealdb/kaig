import hashlib
import logging
from io import BytesIO

from docling_core.types.io import DocumentStream
from pydantic import BaseModel, JsonValue
from surrealdb import RecordID

from demo_unstruct_to_graph.conversion.pdf import convert_and_chunk_pdf
from demo_unstruct_to_graph.definitions import Chunk, EdgeTypes, Tables
from demo_unstruct_to_graph.utils import is_chunk_empty
from kaig.db import DB
from kaig.db.definitions import OriginalDocument

logger = logging.getLogger(__name__)


class Payload(BaseModel):
    doc_id: str


def handler(db: DB, payload: Payload) -> None:
    logger.info("Starting process...")

    record_id = RecordID(Tables.document.value, payload.doc_id)
    document = db.query_one(
        "SELECT * FROM ONLY $record",
        {"record": record_id},
        OriginalDocument,
    )
    if document is None:
        raise ValueError(f"Document not found {record_id}")
    logger.debug(f"Document found: {document}")

    doc_stream = DocumentStream(
        name=document.filename, stream=BytesIO(document.file)
    )

    try:
        if document.content_type == "application/pdf":
            result = convert_and_chunk_pdf(doc_stream)
        else:
            raise ValueError(
                f"Content type {document.content_type} not supported"
            )
    except Exception as e:
        logger.error(f"Error chunking document {record_id}: {e}")
        raise e

    for chunk_text in result.chunks:
        logger.info(f"Processing chunk: {chunk_text[:60]}")
        if is_chunk_empty(chunk_text):
            continue

        hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()
        chunk_id = RecordID(Tables.chunk.value, hash)

        # skip if it already exists
        if db.exists(chunk_id):
            continue

        # ------------------------------------------------------------------
        # -- Embed chunks and insert
        doc = Chunk(content=chunk_text, id=chunk_id)

        try:
            _ = db.embed_and_insert(doc, table=Tables.chunk.value, id=hash)
        except Exception as e:
            logger.error(
                f"Error embedding chunk {chunk_id} with len={len(doc.content)}: {type(e)} {e}"
            )
            raise e

        db.relate(chunk_id, EdgeTypes.CHUNK_FROM_DOC.value.name, record_id)

        # ------------------------------------------------------------------
        # -- Infer concepts in chunk and relate them together
        logger.info(f"inferring concepts {type(db.llm)}")
        if db.llm:
            concepts = db.llm.infer_concepts(chunk_text)
            for concept in concepts:
                concept_id = RecordID(Tables.concept.value, concept)
                _ = db.query_one(
                    "UPSERT ONLY $record",
                    {"record": concept_id},
                    dict[str, JsonValue],
                )
                db.relate(
                    chunk_id,
                    EdgeTypes.MENTIONS_CONCEPT.value.name,
                    concept_id,
                )

    logger.info("Finished process!")
