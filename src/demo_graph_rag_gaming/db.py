from surrealdb import AsyncSurreal

from .embeddings import EmbeddingsGenerator


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
            ON my_table
            FIELDS embedding
            MTREE DIMENSION 384 DIST COSINE TYPE F32
            """)
        await self.db.create("meta:initialized")
        print("Database initialized")

    async def close(self) -> None:
        if not self.db:
            return
        await self.db.close()

    async def insert_embedding(self, embedding: list[float], text: str) -> None:
        if not self.db:
            return
        # TODO: rename table name
        await self.db.create("my_table", {"embedding": embedding, "text": text})

    async def query(
        self, text: str, embeddings_generator: EmbeddingsGenerator
    ) -> list[dict]:
        if not self.db:
            return []
        query_embeddings = embeddings_generator.generate_embeddings(text)
        res = await self.db.query(
            """
            SELECT
                text,
                vector::similarity::cosine(embedding, $vector) AS dist
            FROM my_table
            WHERE embedding <|3|> $vector
            """,
            {"vector": query_embeddings},
        )
        # TODO: remove once fixed in sdk
        assert isinstance(res, list)  # fixes wrong result type from surreal sdk
        return res
