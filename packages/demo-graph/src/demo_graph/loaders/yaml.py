from typing import Any
import yaml

from kaig.db import Relations
from kaig.embeddings import Embedder
from kaig.llm import LLM

from ..models import Thing, ThingInferredAttributes, build_thing


def ensure_str(x: Any) -> str:  # pyright: ignore[reportExplicitAny, reportAny]
    if not isinstance(x, str):
        return str(x)  # pyright: ignore[reportAny]
    return x


def load_things_from_yaml(
    llm: LLM, embedder: Embedder, file_path: str
) -> tuple[list[Thing[ThingInferredAttributes]], set[str], Relations]:
    things: list[Thing[ThingInferredAttributes]] = []
    containers: set[str] = set()
    container_rels: Relations = {}
    with open(file_path, "r") as f:
        content = yaml.safe_load(f)  # pyright: ignore[reportAny]
        # -- Things
        for record in content["things"]:  # pyright: ignore[reportAny]
            desc = ensure_str(record["desc"])
            container = ensure_str(record["where"])
            containers.add(container)
            things.append(
                build_thing(
                    desc,
                    container,
                    llm,
                    embedder,
                    None,
                    [],
                    ThingInferredAttributes,
                )
            )
        # -- Containers
        for record in content["containers"]:  # pyright: ignore[reportAny]
            container = ensure_str(record["name"])
            where = ensure_str(record["parent"])
            containers.add(container)
            containers.add(where)
            container_rels[container] = set([where])

    # -- Results
    return things, containers, container_rels
