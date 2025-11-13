import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile

from demo_unstruct_to_graph.db import init_db
from demo_unstruct_to_graph.handlers.upload import upload_handler
from demo_unstruct_to_graph.queue import process_task, take_task

# configure logging for httpx and httpcore to WARNING
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

db = init_db(True)

DEFAULT_DELAY_IN_S = 1
MAX_DELAY_IN_S = 60


async def my_background_loop():
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


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Application is starting up...")
    # Create the background task
    task = asyncio.create_task(my_background_loop())

    yield  # --- This is the point where the application runs ---

    logger.info("Application is shutting down...")
    _ = task.cancel()
    try:
        await task  # Wait for the task to be cancelled
    except asyncio.CancelledError:
        print("Background loop was successfully cancelled.")


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/upload")
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),  # pyright: ignore[reportCallInDefaultInitializer]
):
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No file selected")

    def async_handler() -> None:
        cr = upload_handler(db, file)
        asyncio.run(cr)

    background_tasks.add_task(async_handler)
