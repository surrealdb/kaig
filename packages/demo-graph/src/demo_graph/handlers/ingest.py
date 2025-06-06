import gspread

from kai_graphora.db import DB
from kai_graphora.llm import LLM

from ..models import Thing, ThingInferredAttributes


def _load_things_file(llm: LLM, spreadsheet: str, skip: int) -> list[Thing]:
    gc = gspread.oauth(
        credentials_filename="./packages/demo-graph/secrets/google-cloud-client-secret.json"
    )
    sh = gc.open(spreadsheet)
    records = sh.get_worksheet(0).get_all_records()
    things = []
    for record in records:
        # things.append(Thing.model_validate(record))
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

    # -- For each document to be inserted
    for thing in things:
        # -- Generate embedding vector
        # -- Insert document
        # -- For each related node
        # relations = []
        # for node in relations:
        #     # -- Insert relation
        #     ...
        print(thing)
        db.insert_document(None, thing)
