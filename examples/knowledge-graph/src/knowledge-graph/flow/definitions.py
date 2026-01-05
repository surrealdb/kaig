from typing import Any

from pydantic import BaseModel, Field
from surrealdb import Value

from kaig.definitions import SerializableRecordID


def IsNone(value: Any | None):  # pyright: ignore[reportExplicitAny]
    return value is None


class Flow(BaseModel):
    id: SerializableRecordID = Field(exclude=True)
    table: str
    dependencies: list[str]
    stamp: str
    priority: int
    hash: int

    @property
    def name(self) -> str:
        id = str(self.id.id) if self.id else "Unknown"  # pyright: ignore[reportAny]
        return id if id else "Unknown"


type Record = dict[str, Value]
