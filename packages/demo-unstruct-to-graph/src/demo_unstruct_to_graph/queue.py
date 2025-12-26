import logging
from enum import Enum
from textwrap import dedent

from pydantic import BaseModel
from surrealdb import Value

from demo_unstruct_to_graph.definitions import Tables
from demo_unstruct_to_graph.handlers.chunk import chunking_handler
from demo_unstruct_to_graph.handlers.inference import inferrence_handler
from demo_unstruct_to_graph.handlers.summarize import summarize_handler
from kaig.db import DB
from kaig.definitions import (
    RecordID as OwnRecordID,
)

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class TaskType(str, Enum):
    chunk = "chunk"
    infer = "infer"
    summarize = "summarize"


class Task(BaseModel):
    id: OwnRecordID
    task: TaskType
    ref: OwnRecordID  # could point to a document, a chunk, a summary, ...
    detail: str | None = None
    status: TaskStatus = TaskStatus.pending


def take_task(db: DB) -> Task | None:
    task = db.query_one(
        dedent(f"""
            SELECT * FROM ONLY {Tables.queue.value}
            WHERE status = "pending"
            ORDER BY time.updated_at ASC
            LIMIT 1
        """),
        {},
        Task,
    )

    # set status to processing
    if task is not None:
        try:
            update_task_status(db, task.id, TaskStatus.processing)
        except Exception as e:
            logger.error(
                f"Error setting task status to processing, but continuing: {e}"
            )

    return task


def update_task_status(
    db: DB, task_id: OwnRecordID, status: str, detail: str | None = None
) -> None:
    _ = db.query_one(
        "UPDATE ONLY $record SET status = $status",
        {"record": task_id, "status": status, "detail": detail},
        dict[str, Value],
    )


def process_task(db: DB, task: Task) -> None:
    failed = False
    try:
        if (
            task.task == "chunk"
            and task.ref.table_name == Tables.document.value
        ):
            chunking_handler(db, task.ref)
        elif task.task == "infer" and task.ref.table_name == Tables.chunk.value:
            inferrence_handler(db, task.ref)
        elif (
            task.task == "summarize"
            and task.ref.table_name == Tables.chunk.value
        ):
            summarize_handler(db, task.ref)
        else:
            logger.warning(
                f"Unknown task type: {task.task} or wrong ref type: {task.ref.table_name}"
            )
    except Exception as e:
        failed = True
        logger.error(f"Error processing task {task.ref}: {e}")
        update_task_status(db, task.id, TaskStatus.failed, str(e))
    finally:
        if not failed:
            update_task_status(db, task.id, TaskStatus.processed)
