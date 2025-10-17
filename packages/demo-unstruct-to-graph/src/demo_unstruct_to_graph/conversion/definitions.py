from dataclasses import dataclass


@dataclass
class ChunkDocumentResult:
    filename: str
    pages: list[str]
    chunks_per_page: list[list[str]]
