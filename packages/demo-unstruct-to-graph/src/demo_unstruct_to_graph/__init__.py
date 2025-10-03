import enum
import hashlib
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from surrealdb import RecordID

from demo_unstruct_to_graph.conversion.xlsx import analyze
from kaig.db import (
    DB,
    LLM,
    Relation,
    VectorTableDefinition,
)
from kaig.db import (
    RecordID as OwnRecordID,
)
from kaig.db.definitions import BaseDocument
from kaig.embeddings import Embedder

logger = logging.getLogger(__name__)


class Chunk(BaseDocument):
    id: OwnRecordID


@dataclass
class Document:
    id: RecordID | None
    filename: str


class Tables(enum.Enum):
    chunk = "chunk"
    concept = "concept"
    document = "document"
    page = "page"


class EdgeTypes(enum.Enum):
    CHUNK_FROM_PAGE = Relation(
        "CHUNK_FROM_PAGE", Tables.chunk.value, Tables.page.value
    )
    PAGE_FROM_DOC = Relation(
        "PAGE_FROM_DOC", Tables.page.value, Tables.document.value
    )
    MENTIONS_CONCEPT = Relation(
        "MENTIONS_CONCEPT", Tables.chunk.value, Tables.concept.value
    )


def is_chunk_empty(text: str) -> bool:
    cleaned_string = re.sub(r"\W+", " ", text)
    cleaned_string = cleaned_string.strip()
    return len(cleaned_string) == 0


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

    return db


def main() -> None:
    import sys

    file = sys.argv[1]

    db = init_db(True)

    # Remove this if you don't want to clear all your tables on every run
    db.clear()

    db.init_db()
    _ = db.sync_conn.query(f"DEFINE TABLE {Tables.concept.value}")

    source = Path(file)
    with open(source, "rb") as f:
        # doc_hash = hashlib.md5(f.read().encode("utf-8")).hexdigest()
        md5_hash = hashlib.md5()
        while True:
            c = f.read(4096)
            if not c:
                break
            md5_hash.update(c)
        doc_hash = md5_hash.hexdigest()

    # result = convert(source)
    # chunks = chunk(result.document)
    result = analyze(source)

    doc_id = RecordID(Tables.document.value, doc_hash)
    doc = Document(id=doc_id, filename=source.name)
    _ = db.query_one(
        "CREATE ONLY $record CONTENT $content",
        {"record": doc.id, "content": asdict(doc)},
        Document,
    )
    for i, page in enumerate(result.pages):
        page_hash = hashlib.md5(page.encode("utf-8")).hexdigest()
        page_id = RecordID(Tables.page.value, page_hash)
        _ = db.query_one(
            "CREATE ONLY $record CONTENT $content",
            {"record": page_id, "content": {"page_num": i}},
            dict,
        )
        db.relate(page_id, EdgeTypes.PAGE_FROM_DOC.value.name, doc_id)
        for chunk_text in result.chunks_per_page[i]:
            if is_chunk_empty(chunk_text):
                continue

            hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()
            chunk_id = RecordID(Tables.chunk.value, hash)
            doc = Chunk(content=chunk_text, id=chunk_id)
            _ = db.embed_and_insert(doc, table=Tables.chunk.value, id=hash)
            db.relate(chunk_id, EdgeTypes.CHUNK_FROM_PAGE.value.name, page_id)

            # - infer concepts in chunk
            if db.llm:
                concepts = db.llm.infer_concepts(chunk_text)
                for concept in concepts:
                    concept_id = RecordID(Tables.concept.value, concept)
                    _ = db.query_one(
                        "UPSERT ONLY $record", {"record": concept_id}, dict
                    )
                    db.relate(
                        chunk_id,
                        EdgeTypes.MENTIONS_CONCEPT.value.name,
                        concept_id,
                    )
