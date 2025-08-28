import yaml

from kaig.db import Relations
from kaig.embeddings import Embedder
from kaig.llm import LLM

from ..models import Thing, ThingInferredAttributes, build_thing


def load_things_from_yaml(
    llm: LLM, embedder: Embedder, file_path: str
) -> tuple[list[Thing[ThingInferredAttributes]], set[str], Relations]:
    things: list[Thing[ThingInferredAttributes]] = []
    containers = set()
    container_rels: Relations = {}
    with open(file_path, "r") as f:
        content = yaml.safe_load(f)
        # -- Things
        for record in content["things"]:
            desc = record["desc"]
            container = record["where"]
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
        for record in content["containers"]:
            container = record["name"]
            where = record["parent"]
            containers.add(container)
            containers.add(where)
            container_rels[container] = set([where])

    # -- Results
    return things, containers, container_rels
