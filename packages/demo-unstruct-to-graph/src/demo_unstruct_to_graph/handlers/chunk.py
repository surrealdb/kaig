import hashlib
import logging
from io import BytesIO

import logfire
from surrealdb import RecordID

from demo_unstruct_to_graph.conversion import ConvertersFactory
from demo_unstruct_to_graph.conversion.definitions import DocumentStreamGeneric
from demo_unstruct_to_graph.definitions import Chunk, Tables
from demo_unstruct_to_graph.utils import is_chunk_empty
from kaig.db import DB
from kaig.definitions import OriginalDocument

logger = logging.getLogger(__name__)


def chunking_handler(db: DB, document: OriginalDocument) -> None:
    with logfire.span("Chunking {doc=}", doc=document.id):
        doc_stream = DocumentStreamGeneric(
            name=document.filename, stream=BytesIO(document.file)
        )

        try:
            result = ConvertersFactory.get_converter(
                document.content_type
            ).convert_and_chunk(doc_stream)
        except Exception as e:
            logger.error(f"Error chunking document {document.id}: {e}")
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
            doc = Chunk(
                content=chunk_text, id=chunk_id, doc=document.id, index=i
            )

            try:
                _ = db.embed_and_insert(doc, table=Tables.chunk.value, id=hash)
            except Exception as e:
                logger.error(
                    f"Error embedding chunk {chunk_id} with len={len(doc.content)}: {type(e)} {e}"
                )
                raise e

        logger.info("Finished chunking!")
