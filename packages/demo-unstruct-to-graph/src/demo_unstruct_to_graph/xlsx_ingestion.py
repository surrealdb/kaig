# pyright: reportMissingTypeStubs=false

import hashlib
import logging
from dataclasses import asdict
from pathlib import Path

from pydantic.types import JsonValue
from surrealdb import RecordID

from .conversion import xlsx
from .db import init_db
from .definitions import Chunk, Document, EdgeTypes, Tables
from .utils import is_chunk_empty

logger = logging.getLogger(__name__)


def main() -> None:
    import sys

    file = sys.argv[1]

    db = init_db(True)

    # --------------------------------------------------------------------------
    # -- open file to ingest
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

    # --------------------------------------------------------------------------
    # -- Convert and chunk XLSX
    result = xlsx.convert_and_chunk(source)

    # --------------------------------------------------------------------------
    # -- Create document
    doc_id = RecordID(Tables.document.value, doc_hash)
    doc = Document(id=doc_id, filename=source.name)
    _ = db.query_one(
        "CREATE ONLY $record CONTENT $content",
        {"record": doc.id, "content": asdict(doc)},
        Document,
    )

    # --------------------------------------------------------------------------
    # -- Create page
    for i, page in enumerate(result.pages):
        page_hash = hashlib.md5(page.encode("utf-8")).hexdigest()
        page_id = RecordID(Tables.page.value, page_hash)
        _ = db.query_one(
            "CREATE ONLY $record CONTENT $content",
            {"record": page_id, "content": {"page_num": i}},
            dict[str, JsonValue],
        )
        db.relate(page_id, EdgeTypes.PAGE_FROM_DOC.value.name, doc_id)
        for chunk_text in result.chunks_per_page[i]:
            if is_chunk_empty(chunk_text):
                continue

            # ------------------------------------------------------------------
            # -- Embed chunks and insert
            hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()
            chunk_id = RecordID(Tables.chunk.value, hash)
            doc = Chunk(content=chunk_text, id=chunk_id)
            _ = db.embed_and_insert(doc, table=Tables.chunk.value, id=hash)
            db.relate(chunk_id, EdgeTypes.CHUNK_FROM_PAGE.value.name, page_id)

            # ------------------------------------------------------------------
            # -- Infer concepts in chunk and relate them together
            if db.llm:
                concepts = db.llm.infer_concepts(chunk_text)
                for concept in concepts:
                    concept_id = RecordID(Tables.concept.value, concept)
                    _ = db.query_one(
                        "UPSERT ONLY $record",
                        {"record": concept_id},
                        dict[str, JsonValue],
                    )
                    db.relate(
                        chunk_id,
                        EdgeTypes.MENTIONS_CONCEPT.value.name,
                        concept_id,
                    )
