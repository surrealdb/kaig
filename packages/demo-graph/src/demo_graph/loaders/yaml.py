import yaml

from kai_graphora.db import Relations
from kai_graphora.llm import LLM

from ..models import Thing, _build_thing


def load_things_from_yaml(
    llm: LLM, file_path: str
) -> tuple[list[Thing], set[str], Relations]:
    things = []
    containers = set()
    container_rels: Relations = {}
    with open(file_path, "r") as f:
        content = yaml.safe_load(f)
        # -- Things
        for record in content["things"]:
            desc = record["desc"]
            container = record["where"]
            containers.add(container)
            things.append(_build_thing(desc, container, None, llm))
        # -- Containers
        for record in content["containers"]:
            container = record["name"]
            where = record["parent"]
            containers.add(container)
            containers.add(where)
            container_rels[container] = set([where])

    # -- Results
    return things, containers, container_rels
