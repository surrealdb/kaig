import enum
from dataclasses import dataclass

from surrealdb import RecordID

from kaig.db.definitions import (
    BaseDocument,
    Relation,
)
from kaig.db.definitions import (
    RecordID as OwnRecordID,
)


class Chunk(BaseDocument):
    id: OwnRecordID


@dataclass
class Document:
    id: RecordID | None
    filename: str


class Tables(enum.Enum):
    chunk = "chunk"
    concept = "concept"
    document = "document"
    page = "page"


class EdgeTypes(enum.Enum):
    CHUNK_FROM_PAGE = Relation(
        "CHUNK_FROM_PAGE", Tables.chunk.value, Tables.page.value
    )
    PAGE_FROM_DOC = Relation(
        "PAGE_FROM_DOC", Tables.page.value, Tables.document.value
    )
    MENTIONS_CONCEPT = Relation(
        "MENTIONS_CONCEPT", Tables.chunk.value, Tables.concept.value
    )
