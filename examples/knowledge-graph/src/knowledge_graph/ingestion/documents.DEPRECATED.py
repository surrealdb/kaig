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
    def chunk(record: flow.Record, flow: flow.Flow):  # pyright: ignore[reportUnusedFunction, reportUnusedParameter]
        doc = OriginalDocumentTA.validate_python(record)

        chunking_handler(db, doc, 0.8, 1000)

    @exe.flow("chunk", stamp="concepts_inferred")
    def infer_concepts(record: flow.Record, flow: flow.Flow):  # pyright: ignore[reportUnusedFunction, reportUnusedParameter]
        chunk = Chunk.model_validate(record)

        _ = inferrence_handler(db, chunk)

    await exe.run()
