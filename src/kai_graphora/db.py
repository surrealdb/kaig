import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import (
    Any,
    Callable,
    TypeVar,
)

from pydantic import BaseModel, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from surrealdb import (
    AsyncHttpSurrealConnection,
    AsyncSurreal,
    AsyncWsSurrealConnection,
    BlockingHttpSurrealConnection,
    BlockingWsSurrealConnection,
    Surreal,
)
from surrealdb import (
    RecordID as SurrealRecordID,
)
from typing_extensions import Annotated

from kai_graphora.llm import LLM

T = TypeVar("T", bound="BaseModel")

Relations = dict[str, set[str]]


@dataclass
class Node:
    name: str
    embedding: list[float] | None


class _RecordID:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        def validate_from_str(value: str) -> SurrealRecordID:
            result = SurrealRecordID.parse(value)
            return result

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(SurrealRecordID),
                    from_str_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: instance.__str__()
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())


RecordID = Annotated[SurrealRecordID, _RecordID]


@dataclass
class EmbeddingInput:
    appid: int
    text: str
    embedding: list[float]


@dataclass
class Analytics:
    key: str
    tag: str
    input: str
    output: str
    score: float


class DB:
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        namespace: str,
        database: str,
        # embedding_dimension: int,
        llm: LLM,
        *,
        document_table="document",
        analytics_table="analytics",
        vector_tables: list[str] = ["document"],
    ):
        self._sync_conn = None
        self._async_conn = None
        self.url = url
        self.username = username
        self.password = password
        self.namespace = namespace
        self.database = database
        self.llm = llm
        self._document_table = document_table
        self._analytics_table = analytics_table
        # self._emdedding_dimension = embedding_dimension
        self._vector_tables = vector_tables

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
        return self._sync_conn

    def init_db(self) -> None:
        """This needs to be called to initialise the DB indexes"""

        # Check if the database is already initialized
        is_init = self.sync_conn.query("SELECT * FROM ONLY meta:initialized")

        # TODO: try this instead after the sdk gets fixed
        # is_init = await self.async_conn.select(SurrealRecordID("meta", "initialized"))
        # print(is_init)

        if is_init is not None:
            return

        for vector_table in self._vector_tables:
            print(f"Creating vector index for {vector_table}")
            self.execute(
                "create_indexes.surql",
                None,
                {
                    "dim": self.llm.dimensions,
                    "index_table": vector_table,
                    "index_name": f"{vector_table}_embeddings_index",
                },
            )

        # TODO: define timestamp fields with default values

        self.sync_conn.create("meta:initialized")
        print("Database initialized")

    async def insert_embeddings(self, embeddings: list[EmbeddingInput]) -> None:
        conn = await self.async_conn
        for embedding in embeddings:
            await conn.query(
                "CREATE $record CONTENT $content",
                {
                    "record": SurrealRecordID(
                        "appdata_embeddings", embedding.appid
                    ),
                    "content": asdict(embedding),
                },
            )

    async def async_insert_document(
        self, id: int | str | None, document: BaseModel
    ) -> None:
        conn = await self.async_conn
        await conn.create(
            self._document_table
            if id is None
            else SurrealRecordID(self._document_table, id),
            document.model_dump(by_alias=True),
            # document.dict(by_alias=True),
        )

    def insert_document(self, id: int | str | None, document: T) -> T:
        res = self.sync_conn.create(
            self._document_table
            if id is None
            else SurrealRecordID(self._document_table, id),
            document.model_dump(by_alias=True),
            # document.dict(by_alias=True),
        )
        if isinstance(res, list):
            raise RuntimeError(f"Unexpected result from DB: {res}")
        return type(document).model_validate(res)

    def insert_analytics_data(
        self, key: str, input: str, output: str, score: float, tag: str
    ) -> None:
        try:
            _res = self.sync_conn.insert(
                self._analytics_table,
                asdict(Analytics(key, tag, input, output, score)),
            )
        except Exception:
            # TODO: log error
            ...

    async def safe_insert_error(self, id: int, error: str):
        conn = await self.async_conn
        try:
            await conn.query(
                "CREATE $record CONTENT $content",
                {
                    "record": SurrealRecordID("error", id),
                    "content": {"error": error},
                },
            )
        except Exception as e:
            print(f"Error inserting error record: {e}", file=sys.stderr)

    async def get_document(self, _doc_type: type[T], id: int) -> T | None:
        conn = await self.async_conn
        res = await conn.query(
            "SELECT * FROM ONLY $record",
            {"record": SurrealRecordID(self._document_table, id)},
        )
        if not res:
            return None
        if not isinstance(res, dict):
            raise RuntimeError(f"Unexpected result from DB: {type(res)}")
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
        if isinstance(res, list):
            raise RuntimeError(f"Unexpected result from DB: {res}")
        return [_doc_type.model_validate(record) for record in res]

    async def error_exists(self, appid: int) -> bool:
        conn = await self.async_conn
        res = await conn.query(
            "RETURN record::exists($record)",
            {"record": SurrealRecordID("error", appid)},
        )
        if not isinstance(res, bool):
            raise RuntimeError(f"Unexpected result from DB: {type(res)}")
        return res

    def vector_search(
        self, text: str, query_embeddings: list[float], table: str | None = None
    ) -> list[dict]:
        surql = _load_surql("query_embeddings.surql")
        res = self.sync_conn.query(
            surql,
            {
                "vector": query_embeddings,
                "table": table if table is not None else self._document_table,
            },
        )
        if not isinstance(res, list):
            raise RuntimeError(f"Unexpected result from DB: {res}")
        return res

    async def async_vector_search(
        self, text: str, query_embeddings: list[float], table: str | None = None
    ) -> list[dict]:
        conn = await self.async_conn
        surql = _load_surql("query_embeddings.surql")
        res = await conn.query(
            surql,
            {
                "vector": query_embeddings,
                "table": table if table is not None else self._document_table,
            },
        )
        if not isinstance(res, list):
            raise RuntimeError(f"Unexpected result from DB: {res}")
        return res

    async def async_execute(self, filename: str, vars: dict | None = None):
        conn = await self.async_conn
        surql = _load_surql(filename)
        await conn.query(surql, vars)

    def execute(
        self,
        filename: str,
        vars: dict | None = None,
        template_vars: dict | None = None,
    ):
        surql = _load_surql(filename)
        if template_vars is not None:
            surql = surql.format(**template_vars)
        self.sync_conn.query(surql, vars)

    def relate(
        self,
        in_: SurrealRecordID,
        relation: str,
        out: SurrealRecordID | list[SurrealRecordID],
    ) -> None:
        all = [out] if not isinstance(out, list) else out
        for out in all:
            _res = self.sync_conn.insert_relation(
                relation, {"in": in_, "out": out}
            )
        # TODO: batch relate when supported
        # _res = self.sync_conn.query("relate $in->$rel->$out", {"in":in_, "out":out, "rel":relation})

    def _add_graph_nodes(
        self,
        src_table: str,
        dest_table: str,
        destinations: list[Node],
        edge_name: str,
        relations: Relations,
    ) -> None:
        for dest in destinations:
            node = asdict(dest)
            try:
                self.sync_conn.upsert(
                    SurrealRecordID(dest_table, dest.name), node
                )
            except Exception as e:
                print(f"Failed: {e} with {node}")
        for doc_id, cats in relations.items():
            try:
                self.relate(
                    SurrealRecordID(src_table, doc_id),
                    edge_name,
                    [SurrealRecordID(dest_table, cat) for cat in cats],
                )
            except Exception as e:
                print(f"Failed: {e}")

    def add_graph_nodes(
        self,
        src_table: str,
        dest_table: str,
        destinations: set[str],
        edge_name: str,
        relations: Relations,
    ) -> None:
        node_destinations = [Node(dest, None) for dest in destinations]
        return self._add_graph_nodes(
            src_table,
            dest_table,
            node_destinations,
            edge_name,
            relations,
        )

    def add_graph_nodes_with_embeddings(
        self,
        src_table: str,
        dest_table: str,
        destinations: set[str],
        edge_name: str,
        relations: Relations,
    ) -> None:
        node_destinations = [
            Node(dest, self.llm.gen_embedding_from_desc(dest))
            for dest in destinations
        ]
        return self._add_graph_nodes(
            src_table,
            dest_table,
            node_destinations,
            edge_name,
            relations,
        )


def _load_surql(filename: str) -> str:
    file_path = Path(__file__).parent.parent.parent / "surql" / filename
    with open(file_path, "r") as file:
        return file.read()
