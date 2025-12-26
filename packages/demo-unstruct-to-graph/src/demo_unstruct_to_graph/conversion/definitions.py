from dataclasses import dataclass
from io import BytesIO


@dataclass
class ChunkDocumentResult:
    filename: str
    chunks: list[str]


@dataclass
class DocumentStreamGeneric:
    name: str
    stream: BytesIO
