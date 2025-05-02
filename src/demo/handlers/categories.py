from demo.db import DB
from demo.handlers.utils import ensure_db_open


@ensure_db_open
async def populate_categories_handler(*, db: DB):
    await db.execute("populate_categories.surql")
