import json
from typing import Any

from kaig.definitions import Relations
from kaig.embeddings import Embedder
from kaig.llm import LLM

from ..models import BookmarkAttributes, Thing, build_thing


def rels_union(a: Relations, b: Relations) -> Relations:
    unified: Relations = {}
    for c in [a, b]:
        for k, v in c.items():
            unified[k] = unified.get(k, set()).union(v)
    return unified


def _parse_bookmark_item(
    item: dict[Any, Any],
    parent: str,
    llm: LLM,
    embedder: Embedder,
) -> tuple[list[Thing[BookmarkAttributes]], Relations]:
    title = item.get("title", "no title")
    assert isinstance(title, str)
    url = item.get("uri")
    if item.get("typeCode") == 1:
        return [
            build_thing(
                title,
                parent,
                llm,
                embedder,
                url,
                item.get("tags", "").split(","),
                BookmarkAttributes,
                "For the tags, use topics you would use to categorize web pages, blog posts, articles, apps, ...",
            )
        ], {title: set([parent])}
    elif item.get("typeCode") == 2:
        # it's a folder
        children = item.get("children", [])
        if isinstance(children, list):
            results: list[Thing[BookmarkAttributes]] = []
            rels = {title: set([parent])}
            for x in children:
                if isinstance(x, dict):
                    things, _rels = _parse_bookmark_item(
                        x, title, llm, embedder
                    )
                    results += things
                    rels = rels_union(rels, _rels)
            return results, rels
    return [], {}


def load_bookmarks_json(
    llm: LLM, embedder: Embedder, file_path: str
) -> tuple[list[Thing[BookmarkAttributes]], set[str], Relations]:
    things: list[Thing[BookmarkAttributes]] = []
    container_rels: Relations = {}
    with open(file_path, "r") as f:
        content = json.load(f)
        for record in content["children"][0]["children"]:
            assert isinstance(record, dict)
            _things, _rels = _parse_bookmark_item(record, "menu", llm, embedder)
            things += _things
            container_rels = rels_union(container_rels, _rels)
    # -- Results
    containers = set(container_rels.keys())
    return things, containers, container_rels
