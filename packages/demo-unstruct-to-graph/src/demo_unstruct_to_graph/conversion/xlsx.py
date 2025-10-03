from dataclasses import dataclass
from pathlib import Path
from typing import override
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import ConversionResult
from docling.document_converter import DocumentConverter, ExcelFormatOption
from docling_core.transforms.chunker.hierarchical_chunker import (
    ChunkingSerializerProvider,
)
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer
from docling_core.types.doc.document import DoclingDocument


@dataclass
class AnalyzeDocumentResult:
    filename: str
    pages: list[str]
    chunks_per_page: list[list[str]]


class MarkdownSerializerProvider(ChunkingSerializerProvider):
    @override
    def get_serializer(self, doc: DoclingDocument):
        return MarkdownDocSerializer(doc=doc)


def convert(source: Path) -> ConversionResult:
    converter = DocumentConverter(
        allowed_formats=[InputFormat.XLSX],
        format_options={InputFormat.XLSX: ExcelFormatOption()},
    )
    result = converter.convert(source)
    return result


def chunk(doc: DoclingDocument) -> list[str]:
    chunker = HybridChunker(serializer_provider=MarkdownSerializerProvider())
    chunk_iter = chunker.chunk(dl_doc=doc)
    chunks = []
    for chunk in chunk_iter:
        enriched_text = chunker.contextualize(chunk=chunk)
        chunks.append(enriched_text)
    return chunks


def analyze(source: Path) -> AnalyzeDocumentResult:
    """Converts and chunks a XLSX document"""
    # -- Convert
    result = convert(source)
    # print(f"tables: {len(result.document.tables)}")
    # print(f"pages: {len(result.pages)}")
    # print(f"document pages: {len(result.document.pages)}")

    # -- Chunks
    page_mds: list[str] = []
    chunks_per_page: list[list[str]] = []

    for page_num in result.document.pages.keys():
        doc_page = result.document.filter(set([page_num]))

        # - markdown
        md = doc_page.export_to_markdown()
        page_mds.append(md)

        # - chunks
        chunks = chunk(doc_page)
        for i, c in enumerate(chunks):
            with open(f"tmp/out/out_chunk_{page_num}_{i}.md", "w") as f:
                _ = f.write(c)
        chunks_per_page.append(chunks)

    return AnalyzeDocumentResult(
        filename=source.name, pages=page_mds, chunks_per_page=chunks_per_page
    )


if __name__ == "__main__":
    import sys

    file = sys.argv[1]

    source = Path(file)
    result = analyze(source)
