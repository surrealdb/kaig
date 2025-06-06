from pydantic import BaseModel


class ThingInferredAttributes(BaseModel):
    brand: str
    category: str
    tags: list[str]


class Thing(BaseModel):
    id: str | None
    name: str
    desc: str
    inferred_attributes: ThingInferredAttributes | None
    embedding: list[float] | None

    def __str__(self) -> str:
        return f"Thing(id={self.id}, name={self.name}, ...)"


class Container(BaseModel):
    id: str
    name: str
