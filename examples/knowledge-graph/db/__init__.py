import logging
from pathlib import Path

from kaig.db import DB
from kaig.definitions import Relation, VectorTableDefinition
from kaig.embeddings import Embedder
from kaig.llm import LLM

from .definitions import Table

logger = logging.getLogger(__name__)


def init_kaig(*, url: str, db: str, ns: str) -> DB:
    tables = [
        Table("file"),
        Table("chunk", has_vector_index=True),
        Table("keyword", has_vector_index=True),
        Table("product", has_vector_index=True),
        Table("category", has_vector_index=True),
        Table("order"),
        Table("review", has_vector_index=True),
        Table("user"),
    ]
    relations = [Relation("REL_FILE_HAS_KEYWORD", "file", "keyword")]
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
    logger.info(f"Connecting to {ns}/{db}")
    db_user = "root"
    db_pass = "root"
    kaig = DB(
        url + "/rpc",
        db_user,
        db_pass,
        ns,
        db,
        embedder,
        llm,
        tables=[t.name for t in tables],
        files_table="file",
        vector_tables=vector_tables,
        graph_relations=relations,
        enable_flow=True,
    )

    surqls: list[str] = []
    tables_dir = Path(__file__).parent.parent / "surql" / "tables"
    for file_path in tables_dir.glob("*.surql"):
        with open(file_path, "r") as file:
            surqls.append(file.read())

    # for surql in surqls:
    #     _ = kaig.sync_conn.query(surql)

    return kaig
