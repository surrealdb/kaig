from pathlib import Path
from typing import override

from demo_unstruct_to_graph.conversion.definitions import ChunkDocumentResult
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import ConversionResult
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.transforms.chunker.hierarchical_chunker import (
    ChunkingSerializerProvider,
)
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer
from docling_core.types.doc.document import DoclingDocument


class MarkdownSerializerProvider(ChunkingSerializerProvider):
    @override
    def get_serializer(self, doc: DoclingDocument):
        return MarkdownDocSerializer(doc=doc)


def convert(source: Path) -> ConversionResult:
    converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={InputFormat.PDF: PdfFormatOption()},
    )
    result = converter.convert(source)
    return result


# TODO: compare this with what's in docling's docs, because this one is based
# on the xlsx.py file and I don't remember if for PDFs the process was more
# straightforward
def chunk(doc: DoclingDocument) -> list[str]:
    chunker = HybridChunker(serializer_provider=MarkdownSerializerProvider())
    chunk_iter = chunker.chunk(dl_doc=doc)
    chunks: list[str] = []
    for chunk in chunk_iter:
        enriched_text = chunker.contextualize(chunk=chunk)
        chunks.append(enriched_text)
    return chunks


def convert_and_chunk(source: Path) -> ChunkDocumentResult:
    """Converts and chunks a PDF document"""
    result = convert(source)

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

    return ChunkDocumentResult(
        filename=source.name, pages=page_mds, chunks_per_page=chunks_per_page
    )


if __name__ == "__main__":
    import sys

    file = sys.argv[1]

    source = Path(file)
    result = convert_and_chunk(source)
    print(result)
