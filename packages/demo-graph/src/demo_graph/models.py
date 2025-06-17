from typing import Literal

from pydantic import BaseModel, Field, model_validator

from kai_graphora.db import RecordID


class ThingInferredAttributes(BaseModel):
    brand: str | None = Field(default=None)
    category: Literal["electronics", "tools", "home", "personal", "office"]
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
    inferred_attributes: ThingInferredAttributes | None = None
    embedding: list[float] | None

    def __str__(self) -> str:
        return f"Thing(id={self.id}, name={self.name}, ...)"

    @classmethod
    def table(cls) -> str:
        return "thing"
