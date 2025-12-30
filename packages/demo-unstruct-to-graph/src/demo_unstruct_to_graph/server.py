import asyncio
import logging
from contextlib import asynccontextmanager
from typing import cast

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from pydantic import TypeAdapter
from surrealdb import Value

from demo_unstruct_to_graph import flow
from demo_unstruct_to_graph.db import init_db
from demo_unstruct_to_graph.definitions import Chunk
from demo_unstruct_to_graph.handlers.chunk import chunking_handler
from demo_unstruct_to_graph.handlers.inference import inferrence_handler
from demo_unstruct_to_graph.handlers.query import query_handler
from demo_unstruct_to_graph.handlers.upload import upload_handler

# from demo_unstruct_to_graph.queue import process_task, take_task
from kaig.db import DB
from kaig.definitions import OriginalDocument

# configure logging for httpx and httpcore to WARNING
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


OriginalDocumentTA = TypeAdapter(OriginalDocument)


async def my_background_loop(db: DB):
    exe = flow.Executor(db)

    @exe.flow("document", {"field": "chunked"}, priority=2)
    def chunk(record: flow.Record):  # pyright: ignore[reportUnusedFunction]
        doc = OriginalDocumentTA.validate_python(record)
        chunking_handler(db, doc)

        # set output field so it's not reprocessed again
        _ = db.sync_conn.query(
            "UPDATE $rec SET chunked = true", {"rec": doc.id}
        )

    @exe.flow("chunk", {"field": "concepts_inferred"})
    def infer_concepts(record: flow.Record):  # pyright: ignore[reportUnusedFunction]
        chunk = Chunk.model_validate(record)
        concepts = inferrence_handler(db, chunk)

        # set output field so it's not reprocessed again
        _ = db.sync_conn.query(
            "UPDATE $rec SET concepts_inferred = $concepts",
            {"rec": chunk.id, "concepts": cast(list[Value], concepts)},
        )

    await exe.run()


class Server:
    def __init__(self):
        @asynccontextmanager
        async def lifespan(_app: FastAPI):
            logger.info("Application is starting up...")
            # Create the background task
            task = asyncio.create_task(my_background_loop(self.db))

            yield  # --- This is the point where the application runs ---

            logger.info("Application is shutting down...")
            _ = task.cancel()
            try:
                await task  # Wait for the task to be cancelled
            except asyncio.CancelledError:
                print("Background loop was successfully cancelled.")

        # ----------------------------------------------------------------------
        self.app: FastAPI = FastAPI(lifespan=lifespan)
        self.db: DB = init_db(True)

        # ----------------------------------------------------------------------
        # Routes

        @self.app.get("/")
        def read_root():  # pyright: ignore[reportUnusedFunction]
            return {"Hello": "World"}

        @self.app.post("/upload")
        async def upload(  # pyright: ignore[reportUnusedFunction]
            background_tasks: BackgroundTasks,
            file: UploadFile = File(...),  # pyright: ignore[reportCallInDefaultInitializer]
        ):
            if file.filename is None:
                raise HTTPException(status_code=400, detail="No file selected")

            def async_handler() -> None:
                cr = upload_handler(self.db, file)
                asyncio.run(cr)

            background_tasks.add_task(async_handler)

        @self.app.post("/query")
        async def query(query: str):  # pyright: ignore[reportUnusedFunction]
            res = await query_handler(self.db, query)
            return {"result": res}


# ------------------------------------------------------------------------------
# FastAPI app
app = Server().app
