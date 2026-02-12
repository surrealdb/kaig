import enum
from dataclasses import dataclass
from typing import Any, ClassVar

from pydantic import ConfigDict
from surrealdb import RecordID

from kaig.definitions import (
    BaseDocument,
    Relation,
)


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


class Tables(enum.Enum):
    chunk = "chunk"
    concept = "concept"
    document = "document"
    page = "page"
    queue = "queue"


class EdgeTypes(enum.Enum):
    MENTIONS_CONCEPT = Relation(
        "MENTIONS_CONCEPT", Tables.chunk.value, Tables.concept.value
    )
