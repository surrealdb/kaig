import gspread
from surrealdb import RecordID

from kai_graphora.db import DB
from kai_graphora.llm import LLM

from ..models import Thing, ThingInferredAttributes


def _load_things_file(llm: LLM, spreadsheet: str, skip: int) -> list[Thing]:
    gc = gspread.oauth(
        credentials_filename="./packages/demo-graph/secrets/google-cloud-client-secret.json"
    )
    sh = gc.open(spreadsheet)
    records = sh.get_worksheet(0).get_all_records()
    # records = records[:1]
    things = []
    for record in records:
        desc = str(record["Item"])
        things.append(
            Thing(
                id=None,
                name=llm.gen_name_from_desc(desc),
                desc=desc,
                inferred_attributes=llm.infer_attributes(
                    desc, ThingInferredAttributes
                ),
                embedding=llm.gen_embedding_from_desc(desc),
            )
        )
    return things


def ingest_things_handler(db: DB, llm: LLM, spreadsheet: str) -> None:
    # TODO: get skip from DB. We should have stored the last read item in the
    # spreahsheet during the last ingestion
    skip = 0
    # -- Load file
    things = _load_things_file(llm, spreadsheet, skip)

    categories = set()
    tags = set()

    # -- For each document to be inserted
    for thing in things:
        # -- Insert document
        doc = db.insert_document(None, thing)
        # -- Collect categories and tags
        if thing.inferred_attributes:
            categories.add(thing.inferred_attributes.category)
            tags = tags.union(thing.inferred_attributes.tags)
            # -- Relate with category
            assert doc.id is not None
            try:
                db.relate(
                    doc.id,
                    "in_category",
                    RecordID("category", thing.inferred_attributes.category),
                )
            except Exception as e:
                print(f"Failed {thing.inferred_attributes.category}: {e}")
            for tag in thing.inferred_attributes.tags:
                try:
                    db.relate(doc.id, "has_tag", RecordID("tag", tag))
                except Exception as e:
                    print(f"Failed {tag}: {e}")
