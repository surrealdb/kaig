from pathlib import Path

from kaig.db import DB


async def populate_categories_handler(*, db: DB):
    file_path = (
        Path(__file__).parent.parent / "surql" / "populate_categories.surql"
    )
    await db.async_execute(file_path)
