import logging

from pydantic import TypeAdapter

# from demo_unstruct_to_graph.queue import process_task, take_task
from kaig.definitions import OriginalDocument

from .. import flow
from ..definitions import Chunk
from ..handlers.chunk import chunking_handler
from ..handlers.inference import inferrence_handler

OriginalDocumentTA = TypeAdapter(OriginalDocument)

logger = logging.getLogger(__name__)


async def ingestion_loop(exe: flow.Executor):
    db = exe.db

    @exe.flow("document", stamp="chunked", priority=2)
    def chunk(record: flow.Record, hash: str):  # pyright: ignore[reportUnusedFunction]
        doc = OriginalDocumentTA.validate_python(record)

        chunking_handler(db, doc)

        # set output field so it's not reprocessed again
        _ = db.sync_conn.query(
            "UPDATE $rec SET chunked = $hash", {"rec": doc.id, "hash": hash}
        )

    @exe.flow("chunk", stamp="concepts_inferred")
    def infer_concepts(record: flow.Record, hash: str):  # pyright: ignore[reportUnusedFunction]
        chunk = Chunk.model_validate(record)

        _ = inferrence_handler(db, chunk)

        # set output field so it's not reprocessed again
        _ = db.sync_conn.query(
            "UPDATE $rec SET concepts_inferred = $hash",
            {"rec": chunk.id, "hash": hash},
        )

    await exe.run()
