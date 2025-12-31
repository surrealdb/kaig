from pydantic import BaseModel
from surrealdb import Value


class Output(BaseModel):
    field: str


class Flow(BaseModel):
    name: str
    table: str
    dependencies: list[str]
    output: Output
    priority: int


type Record = dict[str, Value]
