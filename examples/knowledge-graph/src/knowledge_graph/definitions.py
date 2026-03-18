from dataclasses import dataclass
from typing import Any, ClassVar

from pydantic import ConfigDict
from surrealdb import RecordID

from kaig.definitions import BaseDocument


class Chunk(BaseDocument):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True
    )

    id: RecordID
    doc: RecordID
    index: int
    metadata: dict[str, Any] | None = None  # pyright: ignore[reportExplicitAny]


class Concept(BaseDocument):
    id: RecordID


@dataclass
class Document:
    id: RecordID | None
    filename: str
    content_type: str
    chunking_metadata: dict[str, Any] | None = None  # pyright: ignore[reportExplicitAny]


@dataclass
class Table:
    name: str
    has_vector_index: bool = False
