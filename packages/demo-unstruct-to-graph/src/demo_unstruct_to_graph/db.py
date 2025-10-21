import logging
from pathlib import Path

from kaig.db import DB
from kaig.db.definitions import (
    VectorTableDefinition,
)
from kaig.embeddings import Embedder
from kaig.llm import LLM

from .definitions import EdgeTypes, Tables

logger = logging.getLogger(__name__)


def init_db(init_llm: bool) -> DB:
    tables = [Tables.document.value, Tables.concept.value, Tables.page.value]
    vector_tables = [
        VectorTableDefinition(Tables.chunk.value, "HNSW", "COSINE")
    ]

    logger.info("Init LLM...")
    if init_llm:
        llm = LLM()
    else:
        llm = None
    embedder = Embedder("all-minilm:22m", "F32")

    # -- DB connection
    url = "ws://localhost:8000/rpc"
    db_user = "root"
    db_pass = "root"
    db_ns = "kaig"
    db_db = "demo-unstruct-to-graph"
    db = DB(
        url,
        db_user,
        db_pass,
        db_ns,
        db_db,
        embedder,
        llm,
        tables=tables,
        vector_tables=vector_tables,
        graph_relations=[
            EdgeTypes.CHUNK_FROM_PAGE.value,
            EdgeTypes.PAGE_FROM_DOC.value,
            EdgeTypes.MENTIONS_CONCEPT.value,
        ],
    )
    if llm:
        llm.set_analytics(db.insert_analytics_data)

    # Remove this if you don't want to clear all your tables on every run
    # db.clear()

    surqls = [f"DEFINE TABLE {Tables.concept.value}"]
    for filename in ["handler_chunk_create.surql"]:
        file_path = Path(__file__).parent.parent.parent / "surql" / filename
        with open(file_path, "r") as file:
            surqls.append(file.read())

    db.init_db(surqls)

    return db
