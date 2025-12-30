from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Generic, Literal, TypeVar

from pydantic import BaseModel, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from surrealdb import RecordID as SurrealRecordID
from surrealdb import Value
from typing_extensions import Annotated

Relations = dict[str, set[str]]
Object = Mapping[str, Value]


class _RecordID:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,  # pyright: ignore[reportExplicitAny, reportAny]
        _handler: Callable[[Any], core_schema.CoreSchema],  # pyright: ignore[reportExplicitAny]
    ) -> core_schema.CoreSchema:
        def validate_from_str(value: str) -> SurrealRecordID:
            result = SurrealRecordID.parse(value)
            return result

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(SurrealRecordID),
                    from_str_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())


SerializableRecordID = Annotated[SurrealRecordID, _RecordID]
"""Serializable RecordID"""


class BaseDocument(BaseModel):
    content: str
    embedding: list[float] | None = Field(default=None)


GenericDocument = TypeVar("GenericDocument", bound="BaseDocument")


@dataclass
class Timestamps:
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None


@dataclass
class OriginalDocument:
    id: SerializableRecordID
    filename: str
    content_type: str
    file: bytes
    time: Timestamps | None


@dataclass
class RecursiveResult(Generic[GenericDocument]):
    buckets: list[SurrealRecordID]
    inner: GenericDocument


@dataclass
class Node:
    content: str
    embedding: list[float] | None


@dataclass
class VectorTableDefinition:
    name: str
    index_type: Literal["HNSW", "MTREE"]
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
