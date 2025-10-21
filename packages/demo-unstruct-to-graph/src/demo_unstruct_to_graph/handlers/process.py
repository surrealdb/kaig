import hashlib
import logging
from io import BytesIO

from docling_core.types.io import DocumentStream
from fastapi import HTTPException
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


async def handler(db: DB, payload: Payload) -> None:
    logger.info("Starting process...")

    record_id = RecordID(Tables.document.value, payload.doc_id)
    document = db.query_one(
        "SELECT * FROM ONLY $record",
        {"record": record_id},
        OriginalDocument,
    )
    if document is None:
        raise HTTPException(
            status_code=400, detail=f"Document not found {record_id}"
        )
    logger.debug(f"Document found: {document}")
    logger.info(f"Document found: {document}")

    doc_stream = DocumentStream(
        name=document.filename, stream=BytesIO(document.file)
    )
    if document.content_type == "application/pdf":
        result = convert_and_chunk_pdf(doc_stream)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Content type {document.content_type} not supported",
        )

    # --------------------------------------------------------------------------
    # -- Create page
    for i, page in enumerate(result.pages):
        page_hash = hashlib.md5(page.encode("utf-8")).hexdigest()
        page_id = RecordID(Tables.page.value, page_hash)
        _ = db.query_one(
            "CREATE ONLY $record CONTENT $content",
            {"record": page_id, "content": {"page_num": i}},
            dict[str, JsonValue],
        )
        db.relate(page_id, EdgeTypes.PAGE_FROM_DOC.value.name, record_id)
        for chunk_text in result.chunks_per_page[i]:
            if is_chunk_empty(chunk_text):
                continue

            # ------------------------------------------------------------------
            # -- Embed chunks and insert
            hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()
            chunk_id = RecordID(Tables.chunk.value, hash)
            doc = Chunk(content=chunk_text, id=chunk_id)
            _ = db.embed_and_insert(doc, table=Tables.chunk.value, id=hash)
            db.relate(chunk_id, EdgeTypes.CHUNK_FROM_PAGE.value.name, page_id)

            # ------------------------------------------------------------------
            # -- Infer concepts in chunk and relate them together
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
    # --------------------------------------------------------------------------
    # -- Return
    # return {"doc_id": payload.doc_id, "pages": len(result.pages)}
