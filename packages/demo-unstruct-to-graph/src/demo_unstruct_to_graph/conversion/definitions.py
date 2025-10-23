from dataclasses import dataclass


@dataclass
class ChunkDocumentResult:
    filename: str
    chunks: list[str]
