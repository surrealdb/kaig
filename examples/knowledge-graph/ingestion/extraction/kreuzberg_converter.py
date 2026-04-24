import logging
from pathlib import Path
from typing import Any

from kreuzberg import (
    ChunkingConfig,
    ExtractionConfig,
    KeywordAlgorithm,
    KeywordConfig,
    TokenReductionConfig,
    extract_bytes_sync,
    extract_file_sync,
)
from pydantic import TypeAdapter

from ..utils import safe_path
from .definitions import (
    ChunkDocumentResult,
    ChunkWithMetadata,
    DocumentStreamGeneric,
)

logger = logging.getLogger(__name__)


def _to_chunk_with_metadata(chunks: list[Any]) -> list[ChunkWithMetadata]:  # pyright: ignore[reportExplicitAny]
    return [
        ChunkWithMetadata(content=c.content or "", metadata=c.metadata or {})  # pyright: ignore[reportAny]
        for c in chunks  # pyright: ignore[reportAny]
    ]


# KeywordsTA = TypeAdapter(list[str])
MetadataTA = TypeAdapter(dict[str, Any])  # pyright: ignore[reportExplicitAny]


class KreuzbergConverter:
    def __init__(self, mime_type: str, max_chars: int):
        self._mime_type: str = mime_type
        self._max_chars: int = max_chars

    def _build_config(self, *, min_score: float = 0.8) -> ExtractionConfig:  # pyright: ignore[reportUnknownParameterType]
        """Builds the extraction configuration for the KreuzbergConverter.

        Args:
            min_score (float): The minimum score for a keyword to be included.

        Returns:
            ExtractionConfig: The extraction configuration for the KreuzbergConverter.
        """
        config = ExtractionConfig(
            use_cache=True,
            # this requires feature flag
            keywords=KeywordConfig(
                algorithm=KeywordAlgorithm.Rake,
                max_keywords=5,
                min_score=min_score,
            ),
            output_format="markdown",
            chunking=ChunkingConfig(
                max_chars=int(self._max_chars),
                max_overlap=int(self._max_chars * 0.2),
            ),
            token_reduction=TokenReductionConfig(mode="light"),
            enable_quality_processing=True,
        )
        return config

    @classmethod
    def supports_content_type(cls, content_type: str) -> bool:
        # TODO: add all from https://github.com/kreuzberg-dev/kreuzberg/blob/main/packages/python/README.md#supported-file-formats-56
        supported = ["application/pdf", "text/markdown", "text/html"]
        return content_type in supported

    def convert_and_chunk(
        self,
        name: str,
        source: DocumentStreamGeneric | Path | str,
        keywords_min_score: float,
    ) -> ChunkDocumentResult:
        config = self._build_config(min_score=keywords_min_score)
        if isinstance(source, str):
            result = extract_bytes_sync(
                source.encode(),
                self._mime_type,
                config,  # pyright: ignore[reportUnknownArgumentType]
            )
        elif isinstance(source, Path):
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
        return ChunkDocumentResult(name, chunks, metadata)

    def chunk_markdown(
        self,
        name: str,
        content: str,
        keywords_min_score: float,
    ) -> ChunkDocumentResult:
        config = self._build_config(min_score=keywords_min_score)
        result = extract_bytes_sync(
            content.encode(),
            self._mime_type,
            config=config,  # pyright: ignore[reportUnknownArgumentType]
        )
        metadata = MetadataTA.validate_python(result.metadata)
        logger.info(f"Metadata: {metadata}")
        chunks = _to_chunk_with_metadata(result.chunks)  # pyright: ignore[reportUnknownArgumentType]
        logger.info(f"Chunks: {len(chunks)}")
        return ChunkDocumentResult(name, chunks, metadata)
