import hashlib
import logging
from io import BytesIO

from surrealdb import RecordID

from demo_unstruct_to_graph.conversion import ConvertersFactory
from demo_unstruct_to_graph.conversion.definitions import DocumentStreamGeneric
from demo_unstruct_to_graph.definitions import Chunk, EdgeTypes, Tables
from demo_unstruct_to_graph.utils import is_chunk_empty
from kaig.db import DB
from kaig.db.definitions import OriginalDocument

logger = logging.getLogger(__name__)


def chunking_handler(db: DB, doc_rec_id: RecordID) -> None:
    logger.info("Starting chunking...")

    document = db.query_one(
        "SELECT * FROM ONLY $record",
        {"record": doc_rec_id},
        OriginalDocument,
    )
    if document is None:
        raise ValueError(f"Document not found {doc_rec_id}")
    logger.debug(f"Document found: {document}")

    doc_stream = DocumentStreamGeneric(
        name=document.filename, stream=BytesIO(document.file)
    )

    try:
        result = ConvertersFactory.get_converter(
            document.content_type
        ).convert_and_chunk(doc_stream)
    except Exception as e:
        logger.error(f"Error chunking document {doc_rec_id}: {e}")
        raise e

    for i, chunk_text in enumerate(result.chunks):
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
        doc = Chunk(content=chunk_text, id=chunk_id, index=i)

        try:
            _ = db.embed_and_insert(doc, table=Tables.chunk.value, id=hash)
        except Exception as e:
            logger.error(
                f"Error embedding chunk {chunk_id} with len={len(doc.content)}: {type(e)} {e}"
            )
            raise e

        db.relate(chunk_id, EdgeTypes.CHUNK_FROM_DOC.value.name, doc_rec_id)

    logger.info("Finished chunking!")
