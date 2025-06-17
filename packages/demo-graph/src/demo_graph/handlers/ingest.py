import gspread

from kai_graphora.db import DB, Relations, SurrealRecordID
from kai_graphora.llm import LLM

from ..models import Thing, ThingInferredAttributes


def _load_things_file(
    llm: LLM,
    spreadsheet: str,
    skip: int,
) -> tuple[list[Thing], set[str], Relations]:
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
            Thing(
                id=None,
                name=llm.gen_name_from_desc(desc),
                desc=desc,
                where=container,
                inferred_attributes=llm.infer_attributes(
                    desc,
                    ThingInferredAttributes,
                    "For the `tag`s, used common e-commerce categories",
                ),
                embedding=llm.gen_embedding_from_desc(desc),
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


def ingest_things_handler(db: DB, llm: LLM, spreadsheet: str) -> None:
    # TODO: get skip from DB. We should have stored the last read item in the
    # spreahsheet during the last ingestion
    skip = 0
    # -- Load file
    things, containers, container_rels = _load_things_file(
        llm, spreadsheet, skip
    )

    categories: set[str] = set()
    doc_to_cat: dict[str, set[str]] = {}

    tags: set[str] = set()
    doc_to_tag: dict[str, set[str]] = {}

    # -- For each document to be inserted
    for thing in things:
        # -- Insert document and relate with container
        doc = db.insert_document(None, thing)
        assert doc.id is not None
        db.relate(doc.id, "stored_in", SurrealRecordID("container", doc.where))

        # -- Collect categories and tags
        if thing.inferred_attributes:
            categories.add(thing.inferred_attributes.category)
            tags = tags.union(thing.inferred_attributes.tags)
            key = str(doc.id.id)
            if key not in doc_to_cat:
                doc_to_cat[key] = set()
            doc_to_cat[key].add(thing.inferred_attributes.category)
            if key not in doc_to_tag:
                doc_to_tag[key] = set()
            for tag in thing.inferred_attributes.tags:
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
