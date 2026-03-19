import hashlib
import logging
from io import BytesIO

import logfire
from surrealdb import RecordID

from kaig.db import DB
from kaig.definitions import OriginalDocument

from ..definitions import Chunk
from ..extraction import ConvertersFactory
from ..extraction.definitions import (
    ChunkWithMetadata,
    DocumentStreamGeneric,
)
from ..utils import is_chunk_empty

logger = logging.getLogger(__name__)


def chunking_handler(
    db: DB, document: OriginalDocument, keywords_min_score: float
) -> None:
    with logfire.span("Chunking {doc=}", doc=document.id):
        embedding_model = (
            db.embedder.model_name if db.embedder else "text-embedding-3-small"
        )
        converter = ConvertersFactory.get_converter(
            document.content_type, embedding_model, db.embedder.max_length
        )
        if document.content is not None:
            result = converter.chunk_markdown(
                document.filename,
                document.content,
                keywords_min_score,
            )
        elif document.file is not None:
            doc_stream = DocumentStreamGeneric(
                name=document.filename, stream=BytesIO(document.file)
            )
            result = converter.convert_and_chunk(doc_stream)
        else:
            logger.warning(f"Document {document.id} has no content or file")
            return

        chunks: list[Chunk] = []
        ids: list[str] = []

        for i, chunk in enumerate(result.chunks):
            chunk_text = (
                chunk.content if isinstance(chunk, ChunkWithMetadata) else chunk
            )
            if is_chunk_empty(chunk_text):
                continue

            hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()
            chunk_id = RecordID("chunk", hash)

            # skip if it already exists
            if db.exists(chunk_id):
                continue

            chunk = Chunk(
                content=chunk_text,
                id=chunk_id,
                doc=document.id,
                index=i,
                metadata=chunk.metadata
                if isinstance(chunk, ChunkWithMetadata)
                else None,
            )
            chunks.append(chunk)
            ids.append(hash)

        if chunks:
            _ = db.embed_and_insert_batch(chunks, ids=ids, table="chunk")

        try:
            doc_metadata = result.metadata
            _ = db.sync_conn.query_raw(
                "UPDATE $doc SET chunking_metadata = $metadata RETURN NONE",
                {"metadata": doc_metadata, "doc": document.id},
            )
        except Exception as e:
            logger.error(f"Failed to update document metadata: {e}")

        logger.info("Finished chunking!")
