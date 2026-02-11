import asyncio
import logging
import os

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from kaig.db import DB

from .db import init_db
from .handlers.upload import upload_handler

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
        self.app: FastAPI = FastAPI()

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
