import logging
from pathlib import Path
from typing import Any, override

from kreuzberg import (
    ChunkingConfig,
    ExtractionConfig,
    KeywordAlgorithm,
    KeywordConfig,
    TokenReductionConfig,
    extract_bytes,
    extract_bytes_sync,
    extract_file,
    extract_file_sync,
)
from pydantic import TypeAdapter

from ....utils import safe_path
from ...definitions import (
    ChunkDocumentResult,
    ChunkWithMetadata,
    DocumentStreamGeneric,
)
from ...providers import BaseConverter

logger = logging.getLogger(__name__)

TMP_CHUNK_DIR = Path("tmp/chunks")
TMP_CHUNK_DIR.mkdir(exist_ok=True, parents=True)


def _to_chunk_with_metadata(chunks: list[Any]) -> list[ChunkWithMetadata]:  # pyright: ignore[reportExplicitAny]
    return [
        ChunkWithMetadata(content=c.content or "", metadata=c.metadata or {})  # pyright: ignore[reportAny]
        for c in chunks  # pyright: ignore[reportAny]
    ]


# KeywordsTA = TypeAdapter(list[str])
MetadataTA = TypeAdapter(dict[str, Any])  # pyright: ignore[reportExplicitAny]


class KreuzbergConverter(BaseConverter):
    def __init__(self, mime_type: str):
        self._mime_type: str = mime_type
        # self._embedding_model: str = embedding_model

    def _build_config(self, max_tokens: int = 8191) -> ExtractionConfig:  # pyright: ignore[reportUnknownParameterType]
        config = ExtractionConfig(
            use_cache=True,
            # this requires feature flag
            keywords=KeywordConfig(
                algorithm=KeywordAlgorithm.Yake,
                max_keywords=5,
                min_score=0.2,
            ),
            output_format="markdown",
            chunking=ChunkingConfig(
                max_chars=int(max_tokens * 0.9 * 4),
                max_overlap=int(max_tokens * 0.9 * 4 * 0.2),
            ),
            token_reduction=TokenReductionConfig(mode="light"),
            enable_quality_processing=True,
        )
        return config

    @classmethod
    @override
    def supports_content_type(cls, content_type: str) -> bool:
        # TODO: add all from https://github.com/kreuzberg-dev/kreuzberg/blob/main/packages/python/README.md#supported-file-formats-56
        supported = ["application/pdf", "text/markdown"]
        return content_type in supported

    @override
    def convert_and_chunk(
        self, source: DocumentStreamGeneric | Path
    ) -> ChunkDocumentResult:
        config = self._build_config()
        if isinstance(source, Path):
            source = safe_path(Path("/"), source)
            result = extract_file_sync(source, config=config)  # pyright: ignore[reportUnknownArgumentType]
        else:
            result = extract_bytes_sync(
                source.stream.getbuffer().tobytes(),
                self._mime_type,
                config,  # pyright: ignore[reportUnknownArgumentType]
            )

        logger.info(f"Metadata: {result.metadata}")  # result.metadata.subject
        logger.info(f"Chunks: {len(result.chunks)}")  # pyright: ignore[reportUnknownArgumentType]
        metadata = MetadataTA.validate_python(result.metadata)
        chunks = _to_chunk_with_metadata(result.chunks)  # pyright: ignore[reportUnknownArgumentType]
        return ChunkDocumentResult(source.name, chunks, metadata)

    @override
    async def convert_and_chunk_async(
        self, source: DocumentStreamGeneric | Path
    ) -> ChunkDocumentResult:
        config = self._build_config()
        if isinstance(source, Path):
            source = safe_path(Path("/"), source)
            result = await extract_file(source, config=config)  # pyright: ignore[reportUnknownArgumentType]
        else:
            result = await extract_bytes(
                source.stream.getbuffer().tobytes(),
                self._mime_type,
                config,  # pyright: ignore[reportUnknownArgumentType]
            )

        logger.info(f"Metadata: {result.metadata}")
        metadata = MetadataTA.validate_python(result.metadata)
        chunks = _to_chunk_with_metadata(result.chunks)  # pyright: ignore[reportUnknownArgumentType]
        return ChunkDocumentResult(source.name, chunks, metadata)

    @override
    def chunk_markdown(
        self, source: DocumentStreamGeneric
    ) -> ChunkDocumentResult:
        config = self._build_config()
        result = extract_bytes_sync(
            source.stream.getbuffer().tobytes(),
            mime_type="text/markdown",
            config=config,  # pyright: ignore[reportUnknownArgumentType]
        )
        metadata = MetadataTA.validate_python(result.metadata)
        logger.info(f"metadata: {metadata}")
        chunks = _to_chunk_with_metadata(result.chunks)  # pyright: ignore[reportUnknownArgumentType]
        logger.info(f"chunks: {chunks}")
        return ChunkDocumentResult(source.name, chunks, metadata)
