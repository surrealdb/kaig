import logging
from pathlib import Path

from kaig.db import DB
from kaig.definitions import VectorTableDefinition
from kaig.embeddings import Embedder
from kaig.llm import LLM

from .definitions import Table

logger = logging.getLogger(__name__)


def init_kaig(*, db: str, ns: str) -> DB:
    tables = [Table("file"), Table("chunk", has_vector_index=True)]
    # relations = [Relation("REL_CHUNK_OF_FILE", "chunk", "file")]
    relations = []
    vector_tables = [
        VectorTableDefinition(table.name, "COSINE")
        for table in tables
        if table.has_vector_index
    ]

    # logger.info("Init LLM...")
    llm = LLM(provider="openai", model="gpt-5-mini-2025-08-07", temperature=0.7)
    embedder = Embedder(
        provider="openai",
        model_name="text-embedding-3-small",
        vector_type="F32",
    )

    # -- DB connection
    url = "ws://localhost:8000/rpc"
    db_user = "root"
    db_pass = "root"
    kaig = DB(
        url,
        db_user,
        db_pass,
        ns,
        db,
        embedder,
        llm,
        tables=[t.name for t in tables],
        original_docs_table="file",
        vector_tables=vector_tables,
        graph_relations=relations,
    )
    if llm:
        llm.set_analytics(kaig.insert_analytics_data)

    surqls: list[str] = []
    for filename in ["flow.surql"]:
        file_path = Path(__file__).parent.parent.parent / "surql" / filename
        with open(file_path, "r") as file:
            surqls.append(file.read())

    for surql in surqls:
        _ = kaig.sync_conn.query(surql)

    return kaig
