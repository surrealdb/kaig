from pathlib import Path

from demo_unstruct_to_graph.conversion.definitions import ChunkDocumentResult
from demo_unstruct_to_graph.conversion.generic import convert_and_chunk
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
from docling_core.types.io import DocumentStream


def convert_and_chunk_pdf(source: Path | DocumentStream) -> ChunkDocumentResult:
    """Converts and chunks a PDF document"""
    return convert_and_chunk(source, InputFormat.PDF, PdfFormatOption())
