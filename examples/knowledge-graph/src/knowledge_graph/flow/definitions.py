from typing import Any

from pydantic import BaseModel, Field
from surrealdb import RecordID, Value


def IsNone(value: Any | None):  # pyright: ignore[reportExplicitAny]
    return value is None


class Flow(BaseModel):
    id: RecordID = Field(exclude=True)
    table: str
    dependencies: list[str]
    stamp: str
    priority: int
    hash: str
    rerun_when_updated: bool

    @property
    def name(self) -> str:
        id = str(self.id.id) if self.id else "Unknown"
        return id if id else "Unknown"


type Record = dict[str, Value]
