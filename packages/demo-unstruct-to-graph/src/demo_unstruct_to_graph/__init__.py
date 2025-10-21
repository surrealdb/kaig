import asyncio

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile

import demo_unstruct_to_graph.handlers as handlers
from demo_unstruct_to_graph.db import init_db

db = init_db(True)

app = FastAPI()


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


@app.post("/process")
async def process(
    payload: handlers.process.Payload, background_tasks: BackgroundTasks
):
    def async_handler() -> None:
        cr = handlers.process.handler(db, payload)
        asyncio.run(cr)

    background_tasks.add_task(async_handler)
