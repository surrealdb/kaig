import enum
from dataclasses import dataclass
from typing import ClassVar

from pydantic import ConfigDict
from surrealdb import RecordID

from kaig.definitions import (
    BaseDocument,
    Relation,
    SerializableRecordID,
)


class Chunk(BaseDocument):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True
    )

    id: SerializableRecordID
    doc: RecordID
    index: int
    summary: str | None = None


class Concept(BaseDocument):
    id: SerializableRecordID


@dataclass
class Document:
    id: RecordID | None
    filename: str


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
