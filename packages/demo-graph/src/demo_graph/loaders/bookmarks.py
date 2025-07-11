import json

from kai_graphora.db import Relations
from kai_graphora.llm import LLM

from ..models import Thing, _build_thing


def rels_union(a: Relations, b: Relations) -> Relations:
    unified: Relations = {}
    for c in [a, b]:
        for k, v in c.items():
            unified[k] = unified.get(k, set()).union(v)
    return unified


def _parse_bookmark_item(
    item: dict, parent: str, llm: LLM
) -> tuple[list[Thing], Relations]:
    title = item.get("title", "no title")
    url = item.get("uri")
    if item.get("typeCode") == 1:
        return [
            _build_thing(
                title,
                parent,
                llm,
                url,
                item.get("tags", "").split(","),
                "For the tags, use topics you would use to categorize web pages, blog posts, articles, apps, ...",
            )
        ], {parent: set([title])}
    elif item.get("typeCode") == 2:
        # it's a folder
        children = item.get("children", [])
        if isinstance(children, list):
            results = []
            rels = {parent: set([title])}
            for x in children:
                things, _rels = _parse_bookmark_item(x, title, llm)
                results += things
                rels = rels_union(rels, _rels)
            return results, rels
    return [], {}


def load_bookmarks_json(
    llm: LLM, file_path: str
) -> tuple[list[Thing], set[str], Relations]:
    things = []
    container_rels: Relations = {}
    with open(file_path, "r") as f:
        content = json.load(f)
        for record in content["children"][0]["children"]:
            _things, _rels = _parse_bookmark_item(record, "menu", llm)
            things += _things
            container_rels = rels_union(container_rels, _rels)
    # -- Results
    containers = set(container_rels.keys())
    return things, containers, container_rels
