import sys

from surrealdb import AsyncSurreal, RecordID

from demo_graph_rag_gaming.models import AppData


class DB:
    def __init__(self):
        self.db = None

    async def ensure_open(self) -> None:
        if self.db:
            return
        # TODO: get from env vars
        self.db = AsyncSurreal("ws://localhost:8000")
        await self.db.signin({"username": "demo", "password": "demo"})
        await self.db.use("demo", "demo")
        await self._init_db()

    async def _init_db(self) -> None:
        if not self.db:
            return
        # Check if the database is already initialized
        is_init = await self.db.query("SELECT * FROM ONLY meta:initialized")

        # TODO: try this instead after the sdk gets fixed
        # is_init = await self.db.select(RecordID("meta", "initialized"))
        # print(is_init)

        if is_init is not None:
            return

        await self.db.query("""
            DEFINE INDEX mt_pts
            ON appdata_raw
            FIELDS embedding
            MTREE DIMENSION 384 DIST COSINE TYPE F32
            """)
        await self.db.create("meta:initialized")
        print("Database initialized")

    async def close(self) -> None:
        if not self.db:
            return
        await self.db.close()

    async def insert_embedding(
        self, appid: int, embedding: list[float], text: str
    ) -> None:
        if not self.db:
            return
        await self.db.create(
            "appdata_raw", {"embedding": embedding, "text": text, "appid": appid}
        )

    async def insert_appdata(self, appid: int, appdata: AppData) -> None:
        if not self.db:
            return
        # -- This looks like a bug in the SDK
        # - This doesn't work. Both add the appid as a string, e.g. appdata:⟨123⟩ instead of appdata:123
        # await self.db.create(str(RecordID("appdata", appid)), appdata.dict())
        # await self.db.create(f"appdata:{appid}", appdata.dict())
        # - But this does
        await self.db.query(
            "CREATE $record CONTENT $content",
            {
                "record": RecordID("appdata", appid),
                "content": appdata.dict(by_alias=True),
            },
        )

    async def safe_insert_error(self, appid: int, error: str):
        if not self.db:
            return
        try:
            await self.db.query(
                "CREATE $record CONTENT $content",
                {
                    "record": RecordID("error", appid),
                    "content": {"error": error},
                },
            )
        except Exception as e:
            print(f"Error inserting error record: {e}", file=sys.stderr)

    async def get_appdata(self, appid: int) -> AppData | None:
        if not self.db:
            return None
        # await self.db.select(str(RecordID("appdata", appid)))
        res = await self.db.query(
            "SELECT * FROM ONLY $record",
            {"record": RecordID("appdata", appid)},
        )
        if not res:
            return None
        # TODO: remove once fixed in sdk
        assert isinstance(res, dict), (
            f"Unexpected result type from surreal db: {type(res)}"
        )  # fixes wrong result type from surreal sdk
        return AppData.model_validate(res)

    async def error_exists(self, appid: int) -> bool:
        if not self.db:
            return False
        res = await self.db.query(
            "RETURN record::exists($record)", {"record": RecordID("error", appid)}
        )
        assert isinstance(res, bool), (
            f"Unexpected result type from surreal db: {type(res)}"
        )  # fixes wrong result type from surreal sdk
        return res

    async def query(self, text: str, query_embeddings: list[float]) -> list[dict]:
        if not self.db:
            return []
        res = await self.db.query(
            """
            SELECT
                text,
                vector::similarity::cosine(embedding, $vector) AS dist
            FROM appdata_raw
            WHERE embedding <|3|> $vector
            """,
            {"vector": query_embeddings},
        )
        # TODO: remove once fixed in sdk
        assert isinstance(res, list)  # fixes wrong result type from surreal sdk
        return res
