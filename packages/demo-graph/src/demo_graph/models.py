from typing import Literal

from pydantic import BaseModel, Field, model_validator

from kai_graphora.db import RecordID
from kai_graphora.llm import LLM


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


class Thing(BaseModel):
    id: RecordID | None
    name: str
    desc: str
    where: str
    url: str | None = None
    tags: list[str]
    inferred_attributes: ThingInferredAttributes | None = None
    embedding: list[float] | None
    similarity: float | None = None

    def __str__(self) -> str:
        return f"Thing(id={self.id}, name={self.name}, ...)"

    @classmethod
    def table(cls) -> str:
        return "thing"


def _build_thing(
    desc: str,
    container: str,
    llm: LLM,
    url: str | None,
    tags: list[str],
    additional_instructions: str | None = None,
) -> Thing:
    thing = Thing(
        id=None,
        name=llm.gen_name_from_desc(desc),
        desc=desc,
        where=container,
        url=url,
        tags=tags,
        inferred_attributes=llm.infer_attributes(
            desc, ThingInferredAttributes, additional_instructions
        ),
        embedding=llm.gen_embedding_from_desc(desc),
    )
    return thing
