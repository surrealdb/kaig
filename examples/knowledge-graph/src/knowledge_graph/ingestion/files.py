import logging

from knowledge_graph.handlers.chunk import chunking_handler
from pydantic import TypeAdapter

from kaig.definitions import OriginalDocument

from .. import flow

logger = logging.getLogger(__name__)


MarkdownFileTA = TypeAdapter(OriginalDocument)


async def ingestion_loop(exe: flow.Executor):
    @exe.flow("file", stamp="chunked", rerun_when_updated=False)
    def chunk(record: flow.Record, hash: str):  # pyright: ignore[reportUnusedFunction]
        _v = "1"  # bumping this version number forces reprocessing because the function hash changes

        doc = MarkdownFileTA.validate_python(record)

        # treat mdx as markdown
        if doc.content_type == "text/mdx":
            doc.content_type = "text/markdown"

        # skip folders and empty files (but still mark them as chunked)
        if doc.content_type != "folder" and doc.file is not None:
            chunking_handler(exe.db, doc, 0.8)
        else:
            logger.info(
                f"Skipping chunking for {doc.filename} (content_type={doc.content_type})"
            )

        # set output field so it's not reprocessed again
        res = exe.db.sync_conn.query(
            "UPDATE $rec SET chunked = $hash", {"rec": doc.id, "hash": hash}
        )
        assert isinstance(res, list), f"Expected list, got {res}"
        assert isinstance(res[0], dict), f"Expected dict, got {type(res[0])}"
        assert res[0].get("chunked") == hash, (
            f"Expected hash {hash}, got {res[0].get('chunked')}"
        )

    await exe.run()
