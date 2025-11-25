from abc import ABC, abstractmethod

from demo_unstruct_to_graph.conversion.definitions import (
    ChunkDocumentResult,
    DocumentStreamGeneric,
)


class BaseConverter(ABC):
    @staticmethod
    def supported() -> list[str]:
        return ["application/pdf", "application/xlsx"]

    @abstractmethod
    def convert_and_chunk(
        self, source: DocumentStreamGeneric
    ) -> ChunkDocumentResult: ...

    @classmethod
    def supports_content_type(cls, content_type: str) -> bool:
        return content_type in cls.supported()
