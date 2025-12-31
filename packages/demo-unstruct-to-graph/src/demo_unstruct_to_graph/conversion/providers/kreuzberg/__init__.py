from pathlib import Path
from typing import override

from kreuzberg import (
    ExtractionConfig,
    extract_bytes,
    extract_bytes_sync,
    extract_file,
    extract_file_sync,
)

from demo_unstruct_to_graph.conversion.definitions import (
    ChunkDocumentResult,
    DocumentStreamGeneric,
)
from demo_unstruct_to_graph.conversion.providers import BaseConverter
from demo_unstruct_to_graph.utils import safe_path

TMP_CHUNK_DIR = Path("tmp/chunks")
TMP_CHUNK_DIR.mkdir(exist_ok=True, parents=True)


class KreuzbergConverter(BaseConverter):
    def __init__(self, model_name: str, mime_type: str):
        self._model_name: str = model_name
        self._max_tokens: int = 512
        self._mime_type: str = mime_type

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
        config = ExtractionConfig(
            chunk_content=True,
            use_cache=True,
            # enable_quality_processing=True
        )
        if isinstance(source, Path):
            source = safe_path(Path("/"), source)
            result = extract_file_sync(source, config=config)
        else:
            result = extract_bytes_sync(
                source.stream.getbuffer().tobytes(), self._mime_type, config
            )

        print(f"Content: {result.content}")
        print(f"Metadata: {result.metadata}")

        for i, c in enumerate(result.chunks):
            outfile = (
                TMP_CHUNK_DIR / f"out_chunk_kreuzberg_{source.name}_{i}.md"
            )
            outfile = safe_path(TMP_CHUNK_DIR, outfile)
            with open(outfile, "w", encoding="utf-8") as f:
                _ = f.write(c)

        return ChunkDocumentResult(source.name, result.chunks)

    @override
    async def convert_and_chunk_async(
        self, source: DocumentStreamGeneric | Path
    ) -> ChunkDocumentResult:
        config = ExtractionConfig(
            use_cache=True
            # enable_quality_processing=True
        )
        if isinstance(source, Path):
            source = safe_path(Path("/"), source)
            result = await extract_file(source, config=config)
        else:
            result = await extract_bytes(
                source.stream.getbuffer().tobytes(), self._mime_type, config
            )

        print(f"Content: {result.content}")
        print(f"Metadata: {result.metadata}")

        return ChunkDocumentResult(source.name, result.chunks)
