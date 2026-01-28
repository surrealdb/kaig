import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from kaig.db import DB

from . import flow
from .db import init_db
from .handlers.upload import upload_handler
from .ingestion import ingestion_loop

# DB selection
db_name = os.environ.get("DB_NAME")
if not db_name:
    raise ValueError("DB_NAME environment variable is not set")

# configure logging for httpx and httpcore to WARNING
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class Server:
    def __init__(self, db_name: str):
        self.db: DB = init_db(True, db_name)
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


# ------------------------------------------------------------------------------
# FastAPI app

app = Server(db_name).app
