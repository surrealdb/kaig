import logging
from typing import cast

from pydantic import TypeAdapter
from surrealdb import Value

from kaig import flow
from kaig.definitions import OriginalDocument, Relations

from .chunk import chunking_handler
from .utils import clean_keywords

logger = logging.getLogger(__name__)


FileTA = TypeAdapter(OriginalDocument)


async def ingestion_loop(exe: flow.Executor):
    @exe.flow("file", stamp="flow_chunked", rerun_when_updated=True)
    def chunk(record: flow.Record, flow: flow.Flow):  # pyright: ignore[reportUnusedFunction, reportUnusedParameter]
        _v = "1"  # bumping this version number forces reprocessing because the function hash changes
        chunk_max_chars = 1000

        file = FileTA.validate_python(record)

        # treat mdx as markdown
        if file.content_type == "text/mdx":
            file.content_type = "text/markdown"

        # skip folders and empty files (but still mark them as chunked)
        if file.content_type != "folder" and (
            file.file is not None or file.content is not None
        ):
            # delete existing chunks for this file
            _ = exe.db.sync_conn.query(
                "DELETE FROM chunk WHERE doc = $file", {"file": file.id}
            )

            # create and store chunks
            chunking_handler(exe.db, file, 0.8, chunk_max_chars)
        else:
            logger.info(
                f"Skipping chunking for {file.filename} (content_type={file.content_type})"
            )

    @exe.flow(
        "file",
        stamp="flow_keywords",
        dependencies=["chunking_metadata"],
        rerun_when_updated=True,
    )
    def relate_keywords(record: flow.Record, flow: flow.Flow):  # pyright: ignore[reportUnusedFunction, reportUnusedParameter]
        _v = "1"  # bumping this version number forces reprocessing because the function hash changes
        file = FileTA.validate_python(record)
        file_id = str(file.id.id)
        metadata = record.get("chunking_metadata")

        # insert nodes and edges
        relations: Relations = {}
        keywords: set[str] = set()
        if metadata is not None and isinstance(metadata, dict):
            keyword_objs = metadata.get("keywords")
            if isinstance(keyword_objs, list):
                for kw in keyword_objs:
                    if isinstance(kw, dict):
                        keywords.add(clean_keywords(str(kw.get("text"))))
            relations[file_id] = keywords
        exe.db.add_graph_nodes_with_embeddings(
            "file", "keyword", "REL_FILE_HAS_KEYWORD", relations
        )

    @exe.flow("product", stamp="flow_embedded")
    def embed_products(record: flow.Record, flow: flow.Flow):
        description = record.get("description")
        if exe.db.embedder is None:
            return
        embedding = exe.db.embedder.embed(str(description))
        _ = exe.db.query_one(
            "UPDATE $record SET embedding = $embedding",
            {"record": record.get("id"), "embedding": cast(Value, embedding)},
            dict,
        )

    @exe.flow("review", stamp="flow_sentiment")
    def sentiment(record: flow.Record, flow: flow.Flow):
        text = record.get("text")
        if exe.db.llm is None:
            return
        sentiment = exe.db.llm.sentiment(str(text))
        _ = exe.db.query_one(
            "UPDATE $record SET sentiment = $sentiment",
            {"record": record.get("id"), "sentiment": sentiment},
            dict,
        )

    # --------------------------------------------------------------------------
    await exe.run(max_delay_in_s=5)
