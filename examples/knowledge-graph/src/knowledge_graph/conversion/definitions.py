from dataclasses import dataclass
from io import BytesIO
from typing import Any


@dataclass
class ChunkWithMetadata:
    content: str
    metadata: dict[str, Any]  # pyright: ignore[reportExplicitAny]


@dataclass
class ChunkDocumentResult:
    filename: str
    chunks: list[str] | list[ChunkWithMetadata]


@dataclass
class DocumentStreamGeneric:
    name: str
    stream: BytesIO
