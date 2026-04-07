import hashlib
import logging
from io import BytesIO

import logfire
from surrealdb import RecordID

from kaig.db import DB
from kaig.definitions import OriginalDocument

from ..definitions import Chunk
from ..extraction.definitions import (
    ChunkWithMetadata,
    DocumentStreamGeneric,
)
from ..extraction.kreuzberg_converter import KreuzbergConverter
from ..utils import is_chunk_empty

logger = logging.getLogger(__name__)


def chunking_handler(
    db: DB,
    document: OriginalDocument,
    keywords_min_score: float,
    chunk_max_chars: int,
) -> None:
    if db.embedder is None:
        raise ValueError("Embedder is not configured")
    with logfire.span("Chunking {doc=}", doc=document.id):
        converter = KreuzbergConverter(document.content_type, chunk_max_chars)
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
            result = converter.convert_and_chunk(
                document.filename, doc_stream, keywords_min_score
            )
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
