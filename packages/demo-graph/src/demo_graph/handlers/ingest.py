import gspread

from kai_graphora.db import DB, Relations, SurrealRecordID
from kai_graphora.embeddings import Embedder
from kai_graphora.llm import LLM

from ..loaders.bookmarks import load_bookmarks_json
from ..loaders.yaml import load_things_from_yaml
from ..models import Thing, ThingInferredAttributes, build_thing


def _load_things_file(
    llm: LLM,
    embedder: Embedder,
    spreadsheet: str,
    skip: int,
) -> tuple[list[Thing[ThingInferredAttributes]], set[str], Relations]:
    gc = gspread.oauth(
        credentials_filename="./packages/demo-graph/secrets/google-cloud-client-secret.json"
    )
    sh = gc.open(spreadsheet)

    # -- Things
    records = sh.get_worksheet(0).get_all_records()
    things = []
    containers = set()
    for record in records:
        desc = str(record["Item"])
        container = str(record["Where"])
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
                additional_instructions="For the tags, use common e-commerce categories",
            )
        )

    # -- Containers
    records = sh.get_worksheet(1).get_all_records()
    containers: set[str] = set()
    container_rels: dict[str, set[str]] = {}
    for record in records:
        container = str(record["Container"])
        where = str(record["Where"])
        containers.add(container)
        containers.add(where)
        container_rels[container] = set([where])

    # -- Results
    return things, containers, container_rels


def ingest_things_handler(
    db: DB,
    llm: LLM,
    *,
    spreadsheet: str | None = None,
    yaml_file: str | None = None,
    bookmarks: str | None = None,
) -> None:
    # TODO: get skip from DB. We should have stored the last read item in the
    # spreahsheet during the last ingestion
    skip = 0
    if spreadsheet is not None:
        # -- Load from google spreadsheet
        things, containers, container_rels = _load_things_file(
            llm, db.embedder, spreadsheet, skip
        )
    elif yaml_file is not None:
        # -- Load from yaml
        things, containers, container_rels = load_things_from_yaml(
            llm, db.embedder, yaml_file
        )
    elif bookmarks is not None:
        # -- Load from bookmarks json
        things, containers, container_rels = load_bookmarks_json(
            llm, db.embedder, bookmarks
        )
    else:
        raise ValueError("No input provided")

    categories: set[str] = set()
    doc_to_cat: dict[str, set[str]] = {}

    tags: set[str] = set()
    doc_to_tag: dict[str, set[str]] = {}

    # -- For each document to be inserted
    for thing in things:
        # -- Insert document and relate with container
        doc = db.insert_document(thing)
        doc_id = doc.id
        assert (
            doc_id is not None
        )  # we know it's not None because it just came from the DB
        db.relate(doc_id, "stored_in", SurrealRecordID("container", doc.where))

        # -- Collect categories and tags
        key = str(doc_id.id)
        if key not in doc_to_tag:
            doc_to_tag[key] = set()
        # inferred tags
        inferred_attrs = thing.inferred_attributes
        if inferred_attrs is not None:
            categories.add(inferred_attrs.category)
            tags.update(inferred_attrs.tags)
            if key not in doc_to_cat:
                doc_to_cat[key] = set()
            doc_to_cat[key].add(inferred_attrs.category)
            for tag in inferred_attrs.tags:
                doc_to_tag[key].add(tag)

    db.add_graph_nodes_with_embeddings(
        "document",
        "category",
        categories,
        "in_category",
        doc_to_cat,
    )
    db.add_graph_nodes_with_embeddings(
        "document",
        "tag",
        tags,
        "has_tag",
        doc_to_tag,
    )
    db.add_graph_nodes(
        "container",
        "container",
        containers,
        "stored_in",
        container_rels,
    )
