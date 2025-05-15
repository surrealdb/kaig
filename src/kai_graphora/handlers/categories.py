from kai_graphora.db import DB
from kai_graphora.handlers.utils import ensure_db_open


@ensure_db_open
async def populate_categories_handler(*, db: DB):
    await db.execute("populate_categories.surql")
