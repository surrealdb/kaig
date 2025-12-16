import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import (
    APIRouter,
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from demo_unstruct_to_graph.db import init_db
from demo_unstruct_to_graph.handlers.query import query_handler
from demo_unstruct_to_graph.handlers.upload import upload_handler
from demo_unstruct_to_graph.queue import process_task, take_task
from kaig.db import DB

# configure logging for httpx and httpcore to WARNING
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


DEFAULT_DELAY_IN_S = 1
MAX_DELAY_IN_S = 60


async def my_background_loop(db: DB):
    delay = DEFAULT_DELAY_IN_S
    while True:
        logger.info("Background loop is looping")

        task = take_task(db)
        if task is None:
            await asyncio.sleep(delay)
            delay *= 2  # exponential backoff
            delay = min(delay, MAX_DELAY_IN_S)
            continue
        else:
            delay = DEFAULT_DELAY_IN_S

        process_task(db, task)

        await asyncio.sleep(1)


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
        self.router: APIRouter = APIRouter()
        self.db: DB = init_db(True)

        # ----------------------------------------------------------------------
        # Routes

        @self.router.get("/")
        def read_root():  # pyright: ignore[reportUnusedFunction]
            return {"Hello": "World"}

        @self.router.post("/upload")
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

        @self.router.post("/query")
        async def query(query: str):  # pyright: ignore[reportUnusedFunction]
            res = await query_handler(self.db, query)
            return {"result": res}


# ------------------------------------------------------------------------------
# FastAPI app
app = Server().app
