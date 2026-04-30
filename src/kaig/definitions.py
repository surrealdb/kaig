from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field
from surrealdb import RecordID, Value

Relations = dict[str, set[str]]
Object = Mapping[str, Value]


class BaseDocument(BaseModel):
    content: str
    embedding: list[float] | None = Field(default=None)


GenericDocument = TypeVar("GenericDocument", bound="BaseDocument")


@dataclass
class OriginalDocument:
    id: RecordID
    filename: str
    content_type: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    file: bytes | None = None
    content: str | None = None


@dataclass
class RecursiveResult(Generic[GenericDocument]):
    buckets: list[RecordID]
    inner: GenericDocument


@dataclass
class Node:
    content: str
    embedding: list[float] | None


@dataclass
class VectorTableDefinition:
    name: str
    dist_func: Literal["COSINE"]


@dataclass
class Analytics:
    key: str
    tag: str
    input: str
    output: str
    score: float


@dataclass
class Relation:
    name: str
    in_table: str
    out_table: str


class _SurrealRawError(BaseModel):
    cause: str | None = None
    code: int = 0
    kind: str = ""
    message: str = ""


class _RawQueryResultItem(BaseModel):
    status: str = "ERR"
    time: str
    kind: str
    type: str
    result: Any  # pyright: ignore[reportExplicitAny]


class SurrealRawResponse(BaseModel):
    id: str
    result: list[_RawQueryResultItem] | None = None
    error: _SurrealRawError | None = None
