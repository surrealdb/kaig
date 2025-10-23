import asyncio
import logging
from contextlib import asynccontextmanager
from textwrap import dedent

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from surrealdb import RecordID

import demo_unstruct_to_graph.handlers as handlers
from demo_unstruct_to_graph.db import init_db
from demo_unstruct_to_graph.handlers.process import Payload

logger = logging.getLogger(__name__)
db = init_db(True)


async def my_background_loop():
    while True:
        logger.info("Background loop is looping")

        # take one task from the queue
        task = db.query_one(
            dedent("""
                SELECT * FROM ONLY proc_doc_queue
                WHERE status = None
                ORDER BY time.updated_at ASC
                LIMIT 1
            """),
            {},
            dict,
        )
        if task is not None:
            doc_id = task.get("document")
            proc_doc_id = task.get("id")
            if isinstance(doc_id, RecordID):
                try:
                    handlers.process.handler(db, Payload(doc_id=doc_id.id))
                    _ = db.query_one(
                        'UPDATE ONLY $record SET status = "processed"',
                        {"record": proc_doc_id},
                        dict,
                    )
                except Exception as e:
                    logger.error(f"Error processing document {doc_id}: {e}")
                    _ = db.query_one(
                        'UPDATE ONLY $record SET status = "error", detail = $detail',
                        {"record": proc_doc_id, "detail": str(e)},
                        dict,
                    )
            else:
                logger.warning(f"Invalid document ID: {doc_id}")

        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    background_tasks: BackgroundTasks, file: UploadFile = File(...)
):
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No file selected")

    def async_handler() -> None:
        cr = handlers.upload.handler(db, file)
        asyncio.run(cr)

    background_tasks.add_task(async_handler)
