import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel
from surrealdb import (
    AsyncHttpSurrealConnection,
    AsyncSurreal,
    AsyncWsSurrealConnection,
    BlockingHttpSurrealConnection,
    BlockingWsSurrealConnection,
    RecordID,
    Surreal,
)

T = TypeVar("T", bound="BaseModel")


@dataclass
class EmbeddingInput:
    appid: int
    text: str
    embedding: list[float]


class DB:
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        namespace: str,
        database: str,
        document_table="document",
    ):
        self._sync_conn = None
        self._async_conn = None
        self.url = url
        self.username = username
        self.password = password
        self.namespace = namespace
        self.database = database
        self._document_table = document_table

    @property
    async def async_conn(
        self,
    ) -> AsyncWsSurrealConnection | AsyncHttpSurrealConnection:
        if self._async_conn is None:
            self._async_conn = AsyncSurreal(self.url)
            await self._async_conn.signin(
                {"username": self.username, "password": self.password}
            )
            await self._async_conn.use(self.username, self.database)
            # await self._init_db()
        return self._async_conn

    @property
    def sync_conn(
        self,
    ) -> BlockingHttpSurrealConnection | BlockingWsSurrealConnection:
        if self._sync_conn is None:
            self._sync_conn = Surreal(self.url)
            self._sync_conn.signin(
                {"username": self.username, "password": self.password}
            )
            self._sync_conn.use(self.namespace, self.database)
            # await self._init_db()
        return self._sync_conn

    # TODO: when do we call this?
    def _init_db(self) -> None:
        # Check if the database is already initialized
        is_init = self.sync_conn.query("SELECT * FROM ONLY meta:initialized")

        # TODO: try this instead after the sdk gets fixed
        # is_init = await self.async_conn.select(RecordID("meta", "initialized"))
        # print(is_init)

        if is_init is not None:
            return

        self.execute("create_indexes.surql")
        print("Database initialized")

    async def insert_embeddings(self, embeddings: list[EmbeddingInput]) -> None:
        conn = await self.async_conn
        for embedding in embeddings:
            await conn.query(
                "CREATE $record CONTENT $content",
                {
                    "record": RecordID("appdata_embeddings", embedding.appid),
                    "content": asdict(embedding),
                },
            )

    async def async_insert_document(
        self, id: int | str | None, document: BaseModel
    ) -> None:
        conn = await self.async_conn
        await conn.query(
            "CREATE $record CONTENT $content",
            {
                "record": RecordID(self._document_table, id),
                # "content": document.dict(by_alias=True),
                "content": document.model_dump(by_alias=True),
            },
        )

    def insert_document(
        self, id: int | str | None, document: BaseModel
    ) -> None:
        # self.sync_conn.query(
        #     "CREATE $record CONTENT $content",
        #     {
        #         "record": self._document_table
        #         if id is None
        #         else RecordID(self._document_table, id),
        #         # "content": document.dict(by_alias=True),
        #         "content": document.model_dump(by_alias=True),
        #     },
        # )
        self.sync_conn.create(
            self._document_table if id is None else self._document_table,
            document.model_dump(by_alias=True),
            # document.dict(by_alias=True),
        )

    async def safe_insert_error(self, appid: int, error: str):
        conn = await self.async_conn
        try:
            await conn.query(
                "CREATE $record CONTENT $content",
                {
                    "record": RecordID("error", appid),
                    "content": {"error": error},
                },
            )
        except Exception as e:
            print(f"Error inserting error record: {e}", file=sys.stderr)

    async def get_document(self, _doc_type: type[T], appid: int) -> T | None:
        conn = await self.async_conn
        res = await conn.query(
            "SELECT * FROM ONLY $record",
            {"record": RecordID(self._document_table, appid)},
        )
        if not res:
            return None
        # TODO: remove once fixed in sdk
        assert isinstance(res, dict), (
            f"Unexpected result type from surreal db: {type(res)}"
        )  # fixes wrong result type from surreal sdk
        return _doc_type.model_validate(res)

    async def list_documents(
        self, _doc_type: type[T], start_after: int = 0, limit: int = 100
    ) -> list[T]:
        conn = await self.async_conn
        if start_after == 0:
            res = await conn.query(
                f"SELECT * FROM {self._document_table} ORDER BY id LIMIT $limit",
                {"limit": limit},
            )
        else:
            res = await conn.query(
                f"SELECT * FROM type::thing({self._document_table}, $start_after..) ORDER BY id LIMIT $limit",
                {"limit": limit, "start_after": start_after},
            )
        # TODO: remove once fixed in sdk
        assert isinstance(res, list), (
            f"Unexpected result type from surreal db: {type(res)}"
        )  # fixes wrong result type from surreal sdk
        return [_doc_type.model_validate(record) for record in res]

    async def error_exists(self, appid: int) -> bool:
        conn = await self.async_conn
        res = await conn.query(
            "RETURN record::exists($record)",
            {"record": RecordID("error", appid)},
        )
        assert isinstance(res, bool), (
            f"Unexpected result type from surreal db: {type(res)}"
        )  # fixes wrong result type from surreal sdk
        return res

    async def query(
        self, text: str, query_embeddings: list[float]
    ) -> list[dict]:
        conn = await self.async_conn
        surql = _load_surql("query_embeddings.surql")
        res = await conn.query(
            surql,
            {"vector": query_embeddings},
        )
        # TODO: remove once fixed in sdk
        assert isinstance(res, list)  # fixes wrong result type from surreal sdk
        return res

    async def async_execute(self, filename: str, vars: dict | None = None):
        conn = await self.async_conn
        surql = _load_surql(filename)
        await conn.query(surql, vars)

    def execute(self, filename: str, vars: dict | None = None):
        surql = _load_surql(filename)
        self.sync_conn.query(surql, vars)


def _load_surql(filename: str) -> str:
    file_path = Path(__file__).parent.parent.parent / "surql" / filename
    with open(file_path, "r") as file:
        return file.read()
