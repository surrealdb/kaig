import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from demo_unstruct_to_graph import flow
from demo_unstruct_to_graph.db import init_db
from demo_unstruct_to_graph.handlers.query import query_handler
from demo_unstruct_to_graph.handlers.upload import upload_handler
from demo_unstruct_to_graph.ingestion import ingestion_loop
from kaig.db import DB

# configure logging for httpx and httpcore to WARNING
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class Server:
    def __init__(self):
        self.db: DB = init_db(True)
        self.exe: flow.Executor = flow.Executor(self.db)

        @asynccontextmanager
        async def lifespan(_app: FastAPI):
            logger.info("Application is starting up...")
            task = asyncio.create_task(ingestion_loop(self.exe))

            yield  # --- This is the point where the application runs ---

            logger.info("Application is shutting down...")

            # _ = task.cancel()
            # Call stop instead of cancelling the task
            self.exe.stop()

            try:
                await task
            except asyncio.CancelledError:
                logger.info("Background loop was cancelled during shutdown.")

        # ----------------------------------------------------------------------
        self.app: FastAPI = FastAPI(lifespan=lifespan)

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
