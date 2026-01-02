from pathlib import Path
from typing import override

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

from demo_unstruct_to_graph.utils import safe_path

from ..definitions import (
    ChunkDocumentResult,
    ChunkWithMetadata,
    DocumentStreamGeneric,
)
from ..providers import BaseConverter

TMP_CHUNK_DIR = Path("tmp/chunks")
TMP_CHUNK_DIR.mkdir(exist_ok=True, parents=True)

ChunksTA = TypeAdapter(list[ChunkWithMetadata])


class KreuzbergConverter(BaseConverter):
    def __init__(self, mime_type: str):
        self._mime_type: str = mime_type
        # self._embedding_model: str = embedding_model

    def _build_config(self) -> ExtractionConfig:
        config = ExtractionConfig(
            use_cache=True,
            # TODO: this is not generating any keywords
            keywords=KeywordConfig(
                algorithm=KeywordAlgorithm.Yake, max_keywords=10, min_score=0.1
            ),
            chunking=ChunkingConfig(max_chars=1000, max_overlap=100),
            token_reduction=TokenReductionConfig(mode="light"),
            enable_quality_processing=True,
        )
        return config

    @classmethod
    @override
    def supports_content_type(cls, content_type: str) -> bool:
        # TODO: add all from https://github.com/kreuzberg-dev/kreuzberg/blob/main/packages/python/README.md#supported-file-formats-56
        supported = ["application/pdf"]
        return content_type in supported

    @override
    def convert_and_chunk(
        self, source: DocumentStreamGeneric | Path
    ) -> ChunkDocumentResult:
        config = self._build_config()
        if isinstance(source, Path):
            source = safe_path(Path("/"), source)
            result = extract_file_sync(source, config=config)
        else:
            result = extract_bytes_sync(
                source.stream.getbuffer().tobytes(), self._mime_type, config
            )

        print(f"Chunks: {result.chunks}")
        print(f"Metadata: {result.metadata}")
        print(f"Chunks: {len(result.chunks)}")
        # self._dump_chunks(source.name, result.chunks)

        chunks = ChunksTA.validate_python(result.chunks)

        return ChunkDocumentResult(
            source.name,
            chunks,
            # [ChunkWithMetadata(**chunk) for chunk in result.chunks],
        )

    @override
    async def convert_and_chunk_async(
        self, source: DocumentStreamGeneric | Path
    ) -> ChunkDocumentResult:
        config = self._build_config()
        if isinstance(source, Path):
            source = safe_path(Path("/"), source)
            result = await extract_file(source, config=config)
        else:
            result = await extract_bytes(
                source.stream.getbuffer().tobytes(), self._mime_type, config
            )

        print(f"Content: {result.content}")
        print(f"Metadata: {result.metadata}")
        # self._dump_chunks(source.name, result.chunks)

        return ChunkDocumentResult(source.name, result.chunks)
