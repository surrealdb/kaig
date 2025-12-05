import dataclasses
import logging
from pathlib import Path
from typing import override

import tiktoken
from docling.datamodel.base_models import InputFormat
from docling.document_converter import (
    DocumentConverter,
    ExcelFormatOption,
    PdfFormatOption,
)
from docling_core.transforms.chunker.hierarchical_chunker import (
    ChunkingSerializerProvider,
)
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer
from docling_core.types.doc.document import DoclingDocument
from docling_core.types.io import DocumentStream

from demo_unstruct_to_graph.conversion.definitions import (
    ChunkDocumentResult,
    DocumentStreamGeneric,
)
from demo_unstruct_to_graph.conversion.providers import BaseConverter
from demo_unstruct_to_graph.conversion.providers.docling.merge_chunks import (
    merge_short_chunks,
)
from demo_unstruct_to_graph.conversion.utils import sanitize_filename

logger = logging.getLogger(__name__)

TMP_CHUNK_DIR = Path("tmp/chunks")
TMP_CHUNK_DIR.mkdir(exist_ok=True, parents=True)


class MarkdownSerializerProvider(ChunkingSerializerProvider):
    @override
    def get_serializer(self, doc: DoclingDocument):
        return MarkdownDocSerializer(doc=doc)


def _chunk(doc: DoclingDocument, tokenizer: OpenAITokenizer) -> list[str]:
    chunker = HybridChunker(
        serializer_provider=MarkdownSerializerProvider(),
        tokenizer=tokenizer,
    )
    chunk_iter = chunker.chunk(dl_doc=doc)
    chunks: list[str] = []
    for chunk in chunk_iter:
        enriched_text = chunker.contextualize(chunk=chunk)
        chunks.append(enriched_text)
    return chunks


class DoclingConverter(BaseConverter):
    def __init__(self, model_name: str):
        self._model_name: str = model_name
        self._max_tokens: int = 512

    @classmethod
    @override
    def supports_content_type(cls, content_type: str) -> bool:
        supported = ["application/pdf", "application/xlsx"]
        return content_type in supported

    @override
    def convert_and_chunk(
        self, source: DocumentStreamGeneric | Path
    ) -> ChunkDocumentResult:
        """Converts and chunks a document"""
        tokenizer = OpenAITokenizer(
            tokenizer=tiktoken.encoding_for_model(self._model_name),
            max_tokens=self._max_tokens,
        )

        converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF, InputFormat.XLSX],
            format_options={
                InputFormat.PDF: PdfFormatOption(),
                InputFormat.XLSX: ExcelFormatOption(),
            },
        )
        result = converter.convert(
            source
            if isinstance(source, Path)
            else DocumentStream.model_validate(dataclasses.asdict(source))
        )

        try:
            chunks = _chunk(result.document, tokenizer)
        except Exception as e:
            logger.error(f"Error chunking doc {source.name}: {e}")
            raise e

        # Post-process: merge too-short chunks with neighbours
        chunks = merge_short_chunks(chunks, tokenizer, 60, self._max_tokens)

        for i, c in enumerate(chunks):
            safe_name = sanitize_filename(source.name)
            outfile = TMP_CHUNK_DIR / f"out_chunk_{safe_name}_{i}.md"
            resolved_outfile = outfile.resolve()
            tmpdir_resolved = TMP_CHUNK_DIR.resolve()
            try:
                _ = resolved_outfile.relative_to(tmpdir_resolved)
            except ValueError:
                raise RuntimeError(
                    "Refusing to write outside temp chunk directory."
                )
            with open(resolved_outfile, "w", encoding="utf-8") as f:
                _ = f.write(c)

        return ChunkDocumentResult(filename=source.name, chunks=chunks)


if __name__ == "__main__":
    import sys

    file = sys.argv[1]

    source = Path(file)
    converter = DoclingConverter("text-embedding-3-large")
    result = converter.convert_and_chunk(source)
    print(result)
    print("-------------------------------------------------------------------")
    for j, x in enumerate(result.chunks):
        print(f"  - {j}: {len(x)}")
