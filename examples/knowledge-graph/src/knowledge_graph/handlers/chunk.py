import hashlib
import logging
from io import BytesIO

import logfire
from surrealdb import RecordID

from kaig.db import DB
from kaig.definitions import OriginalDocument

from ..definitions import Chunk, Document, Tables
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
        doc_stream = DocumentStreamGeneric(
            name=document.filename, stream=BytesIO(document.file)
        )

        embedding_model = (
            db.embedder.model_name if db.embedder else "text-embedding-3-small"
        )
        result = ConvertersFactory.get_converter(
            document.content_type, embedding_model
        ).chunk_markdown(
            doc_stream,
            db.embedder.max_length if db.embedder else 8191,
            keywords_min_score,
        )

        chunks: list[Chunk] = []
        ids: list[str] = []

        for i, chunk in enumerate(result.chunks):
            chunk_text = (
                chunk.content if isinstance(chunk, ChunkWithMetadata) else chunk
            )
            if is_chunk_empty(chunk_text):
                continue

            hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()
            chunk_id = RecordID(Tables.chunk.value, hash)

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
            _ = db.embed_and_insert_batch(
                chunks, ids=ids, table=Tables.chunk.value
            )

        try:
            doc_metadata = result.metadata
            _ = db.query_one(
                "UPDATE ONLY $doc SET chunking_metadata = $metadata",
                {"metadata": doc_metadata, "doc": document.id},
                Document,
            )
        except Exception as e:
            logger.error(f"Failed to update document metadata: {e}")

        logger.info("Finished chunking!")
