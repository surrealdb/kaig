from typing import Generic, Literal

from pydantic import BaseModel, Field, model_validator

from kai_graphora.db import RecordID
from kai_graphora.db.definitions import BaseDocument
from kai_graphora.embeddings import Embedder
from kai_graphora.llm import LLM, T_Model


class Document(BaseDocument):
    id: RecordID


class BookmarkAttributes(BaseModel):
    category: Literal["blogs", "apps and tools", "work", "personal", "other"]
    tags: list[str]


class ThingInferredAttributes(BaseModel):
    brand: str | None = Field(default=None)
    category: Literal[
        "electronics",
        "tools",
        "home",
        "personal",
        "office",
        "web bookmark",
        "other",
    ]
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def lower_case_tags(self) -> "ThingInferredAttributes":
        self.tags = [tag.lower() for tag in self.tags]
        return self


class Thing(BaseDocument, Generic[T_Model]):
    id: RecordID | None
    name: str
    content: str
    where: str
    url: str | None = None
    inferred_attributes: T_Model | None = None
    similarity: float | None = None

    def __str__(self) -> str:
        return f"Thing(id={self.id}, name={self.name}, ...)"

    @classmethod
    def table(cls) -> str:
        return "thing"


def build_thing(
    desc: str,
    container: str,
    llm: LLM,
    embedder: Embedder,
    url: str | None,
    tags: list[str],
    attrs_type: type[T_Model],
    additional_instructions: str | None = None,
) -> Thing[T_Model]:
    inferred_attributes = llm.infer_attributes(
        desc,
        attrs_type,
        additional_instructions,
        {"tags": tags, "category": "other"},
    )
    thing = Thing(
        id=None,
        name=llm.gen_name_from_desc(desc),
        content=desc,
        where=container,
        url=url,
        inferred_attributes=inferred_attributes,
        embedding=embedder.embed(desc),
    )
    return thing
