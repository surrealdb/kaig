import hashlib
import logging
from io import BytesIO

from docling_core.types.io import DocumentStream
from surrealdb import RecordID

from demo_unstruct_to_graph.conversion.pdf import convert_and_chunk_pdf
from demo_unstruct_to_graph.definitions import Chunk, EdgeTypes, Tables
from demo_unstruct_to_graph.utils import is_chunk_empty
from kaig.db import DB
from kaig.db.definitions import OriginalDocument

logger = logging.getLogger(__name__)


def chunking_handler(db: DB, doc_rec_id: RecordID) -> None:
    logger.info("Starting chunking...")

    # record_id = RecordID(Tables.document.value, doc_id)
    document = db.query_one(
        "SELECT * FROM ONLY $record",
        {"record": doc_rec_id},
        OriginalDocument,
    )
    if document is None:
        raise ValueError(f"Document not found {doc_rec_id}")
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
        logger.error(f"Error chunking document {doc_rec_id}: {e}")
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

        db.relate(chunk_id, EdgeTypes.CHUNK_FROM_DOC.value.name, doc_rec_id)

    logger.info("Finished chunking!")
