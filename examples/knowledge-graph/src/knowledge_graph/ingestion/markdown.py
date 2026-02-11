import logging

from knowledge_graph.handlers.chunk import chunking_handler
from pydantic import TypeAdapter

from kaig.definitions import OriginalDocument

from .. import flow

logger = logging.getLogger(__name__)


MarkdownFileTA = TypeAdapter(OriginalDocument)


async def ingestion_loop(exe: flow.Executor):
    @exe.flow("document", stamp="chunked", rerun_when_updated=True)
    def chunk(record: flow.Record, hash: str):  # pyright: ignore[reportUnusedFunction]
        _v = "4"
        doc = MarkdownFileTA.validate_python(record)

        # treat mdx as markdown
        if doc.content_type == "text/mdx":
            doc.content_type = "text/markdown"

        # only process markdown files
        if doc.content_type != "text/markdown":
            # _ = exe.db.sync_conn.query(
            #     "UPDATE $rec SET chunked = $hash", {"rec": doc.id, "hash": hash}
            # )
            return

        chunking_handler(exe.db, doc)

        # set output field so it's not reprocessed again
        _ = exe.db.sync_conn.query(
            "UPDATE $rec SET chunked = $hash", {"rec": doc.id, "hash": hash}
        )

    await exe.run()
