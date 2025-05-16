from kai_graphora.db import DB


async def populate_categories_handler(*, db: DB):
    await db.async_execute("populate_categories.surql")
