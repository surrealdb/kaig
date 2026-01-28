import logging
from pathlib import Path

from kaig.db import DB
from kaig.definitions import VectorTableDefinition
from kaig.embeddings import Embedder
from kaig.llm import LLM

from .definitions import EdgeTypes, Tables

logger = logging.getLogger(__name__)


def init_db(init_llm: bool, db_name: str, init_indexes: bool = True) -> DB:
    tables = [Tables.document.value, Tables.concept.value, Tables.page.value]
    vector_tables = [
        VectorTableDefinition(Tables.chunk.value, "HNSW", "COSINE"),
        VectorTableDefinition(Tables.concept.value, "HNSW", "COSINE"),
    ]

    if init_llm:
        logger.info("Init LLM...")
        llm = LLM(
            provider="openai", model="gpt-5-mini-2025-08-07", temperature=1
        )
    else:
        logger.info("Init without LLM")
        llm = None
    embedder = Embedder(
        provider="openai",
        model_name="text-embedding-3-small",
        vector_type="F32",
    )

    # -- DB connection
    url = "ws://localhost:8000/rpc"
    db_user = "root"
    db_pass = "root"
    db_ns = "kaig"
    db_db = db_name
    db = DB(
        url,
        db_user,
        db_pass,
        db_ns,
        db_db,
        embedder,
        llm,
        tables=tables,
        original_docs_table="document",
        vector_tables=vector_tables,
        graph_relations=[EdgeTypes.MENTIONS_CONCEPT.value],
    )
    if llm:
        llm.set_analytics(db.insert_analytics_data)

    # Remove this if you don't want to clear all your tables on every run
    # db.clear()

    surqls: list[str] = []
    for filename in ["schema.surql"]:
        file_path = Path(__file__).parent.parent.parent / "surql" / filename
        with open(file_path, "r") as file:
            surqls.append(file.read())

    for surql in surqls:
        _ = db.sync_conn.query(surql)
    db.init_db(force=init_indexes)

    return db
