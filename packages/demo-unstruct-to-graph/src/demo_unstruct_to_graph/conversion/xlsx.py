from pathlib import Path

from demo_unstruct_to_graph.conversion.definitions import ChunkDocumentResult
from demo_unstruct_to_graph.conversion.generic import convert_and_chunk
from docling.datamodel.base_models import InputFormat
from docling.document_converter import ExcelFormatOption
from docling_core.types.io import DocumentStream


def convert_and_chunk_xlsx(
    source: Path | DocumentStream,
) -> ChunkDocumentResult:
    """Converts and chunks a XLSX document"""
    return convert_and_chunk(source, InputFormat.XLSX, ExcelFormatOption())
