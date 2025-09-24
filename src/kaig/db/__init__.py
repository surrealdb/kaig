import logging
import sys
from dataclasses import asdict
from pathlib import Path

from pydantic import BaseModel, ValidationError
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

from kaig.embeddings import Embedder
from kaig.llm import LLM

from .definitions import (
    Analytics,
    GenericDocument,
    Node,
    Object,
    RecordID,
    RecursiveResult,
    Relation,
    Relations,
    VectorTableDefinition,
)
from .utils import parse_time

logger = logging.getLogger(__name__)


class DB:
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        namespace: str,
        database: str,
        embedder: Embedder | None,
        llm: LLM | None,
        *,
        analytics_table: str = "analytics",
        vector_tables: list[VectorTableDefinition] | None = None,
        graph_relations: list[Relation] | None = None,
    ):
        self._sync_conn: (
            BlockingHttpSurrealConnection | BlockingWsSurrealConnection | None
        ) = None
        self._async_conn: (
            AsyncHttpSurrealConnection | AsyncWsSurrealConnection | None
        ) = None
        self.url: str = url
        self.username: str = username
        self.password: str = password
        self.namespace: str = namespace
        self.database: str = database
        self.embedder: Embedder | None = embedder
        self.llm: LLM | None = llm
        self._analytics_table: str = analytics_table
        self._vector_tables: list[VectorTableDefinition] = vector_tables or []
        self._graph_relations: list[Relation] = graph_relations or []

        self._surql_cache: dict[str, str] = {}
        for filename in [
            "create_index_hnsw.surql",
            "create_index_mtree.surql",
            "define_relation.surql",
            "graph_query_in.surql",
            "graph_siblings.surql",
            "vector_search.surql",
            "vector_search_simple.surql",
        ]:
            self._surql_cache[filename] = self._load_surql(filename)

    def init_db(self) -> None:
        """This needs to be called to initialise the DB indexes"""

        # Check if the database is already initialized
        is_init = self.sync_conn.query("SELECT * FROM ONLY meta:initialized")
        if is_init is not None:
            return

        # vector index cheat sheet: https://surrealdb.com/docs/surrealdb/reference-guide/vector-search#vector-search-cheat-sheet
        if self._vector_tables and self.embedder is None:
            raise ValueError(
                "Embedder is not initialized, and is required for vector tables to be created"
            )
        if self.embedder is not None:
            for vector_table in self._vector_tables:
                match vector_table.index_type:
                    case "HNSW":
                        surql_name = "create_index_hnsw.surql"
                    case _:
                        surql_name = "create_index_mtree.surql"
                _ = self.execute(
                    surql_name,
                    None,
                    {
                        "table": vector_table.name,
                        "dimension": self.embedder.dimension,
                        "distance_function": vector_table.dist_func,
                        "vector_type": self.embedder.vector_type,
                    },
                )

        for relation in self._graph_relations:
            print(f"Creating relation {relation.name}")
            _ = self.execute(
                "define_relation.surql",
                None,
                {
                    "name": relation.name,
                    "in_tb": relation.in_table,
                    "out_tb": relation.out_table,
                },
            )

        # TODO: define timestamp fields with default values

        _ = self.sync_conn.create("meta:initialized")
        print("Database initialized")

    def clear(self) -> None:
        res = self.sync_conn.query("REMOVE TABLE IF EXISTS meta;")
        for table in self._vector_tables:
            res = self.sync_conn.query(f"REMOVE TABLE IF EXISTS {table.name};")
            logger.debug(res)
            res = self.sync_conn.query(
                f"REMOVE INDEX IF EXISTS idx_{table.name} ON {table.name};"
            )
            logger.debug(res)

    @property
    def _vector_table(self) -> str:
        return self._vector_tables[0].name

    # ==========================================================================
    # Connections
    # ==========================================================================

    @property
    async def async_conn(
        self,
    ) -> AsyncWsSurrealConnection | AsyncHttpSurrealConnection:
        if self._async_conn is None:
            self._async_conn = AsyncSurreal(self.url)
            _ = await self._async_conn.signin(
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
            _ = self._sync_conn.signin(
                {"username": self.username, "password": self.password}
            )
            self._sync_conn.use(self.namespace, self.database)
        return self._sync_conn

    # ==========================================================================
    # Execute
    # ==========================================================================

    def _load_surql(self, filename_or_path: str | Path) -> str:
        if isinstance(filename_or_path, Path):
            filename = filename_or_path.name
            file_path = filename_or_path
        else:
            filename = filename_or_path
            file_path = Path(__file__).parent / "surql" / filename_or_path
        # check cache
        cached = self._surql_cache.get(filename)
        if cached is not None:
            return cached
        with open(file_path, "r") as file:
            return file.read()

    def execute(
        self,
        file: str | Path,
        vars: Object | None = None,
        template_vars: Object | None = None,
    ) -> tuple[list[Object] | Object, float]:
        surql = self._load_surql(file)
        if template_vars is not None:
            surql = surql.format(**template_vars)
        res: list[Object] | Object = self.sync_conn.query_raw(surql, vars)
        if "result" in res:
            return res["result"][0]["result"], parse_time(
                res["result"][0]["time"]
            )
        else:
            print(f"unexpected result: {file}: {res}")
            return res, 0

    async def async_execute(
        self,
        file: str | Path,
        vars: Object | None = None,
        template_vars: Object | None = None,
    ) -> tuple[list[Object] | Object, float]:
        surql = self._load_surql(file)
        if template_vars is not None:
            surql = surql.format(**template_vars)
        conn = await self.async_conn
        res: list[Object] | Object = await conn.query_raw(surql, vars)
        if "result" in res:
            return res["result"][0]["result"], parse_time(
                res["result"][0]["time"]
            )
        else:
            print(f"unexpected result: {file}: {res}")
            return res, 0

    # ==========================================================================
    # Analytics
    # ==========================================================================

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
            _ = await conn.query(
                "CREATE $record CONTENT $content",
                {
                    "record": SurrealRecordID("error", id),
                    "content": {"error": error},
                },
            )
        except Exception as e:
            print(f"Error inserting error record: {e}", file=sys.stderr)

    async def error_exists(self, id: str) -> bool:
        conn = await self.async_conn
        res = await conn.query(
            "RETURN record::exists($record)",
            {"record": SurrealRecordID("error", id)},
        )
        if not isinstance(res, bool):
            raise RuntimeError(f"Unexpected result from DB: {type(res)}")
        return res

    # ==========================================================================
    # Documents
    # ==========================================================================

    async def get_document(
        self, doc_type: type[GenericDocument], id: int
    ) -> GenericDocument | None:
        conn = await self.async_conn
        res = await conn.query(
            "SELECT * FROM ONLY $record",
            {"record": SurrealRecordID(self._vector_table, id)},
        )
        if not res:
            return None
        if not isinstance(res, dict):
            raise RuntimeError(f"Unexpected result from DB: {type(res)}")
        return doc_type.model_validate(res)

    async def list_documents(
        self,
        doc_type: type[GenericDocument],
        start_after: int = 0,
        limit: int = 100,
    ) -> list[GenericDocument]:
        conn = await self.async_conn
        if start_after == 0:
            res = await conn.query(
                f"SELECT * FROM {self._vector_table} ORDER BY id LIMIT $limit",
                {"limit": limit},
            )
        else:
            res = await conn.query(
                f"SELECT * FROM type::thing({self._vector_table}, $start_after..) ORDER BY id LIMIT $limit",
                {"limit": limit, "start_after": start_after},
            )
        if not isinstance(res, list):
            raise RuntimeError(f"Unexpected result from DB: {type(res)}")
        return [doc_type.model_validate(record) for record in res]

    # ==========================================================================
    # Vector store
    # ==========================================================================

    # TODO: do we still need this?
    async def async_insert_document(
        self,
        document: BaseModel,
        id: int | str | None = None,
        table: str | None = None,
    ) -> None:
        conn = await self.async_conn
        if not table:
            table = self._vector_table
        _ = await conn.create(
            table if id is None else SurrealRecordID(table, id),
            document.model_dump(by_alias=True),
        )

    def insert_document(
        self,
        document: GenericDocument,
        id: int | str | None = None,
        table: str | None = None,
    ) -> GenericDocument:
        if not table:
            table = self._vector_table
        res = self.sync_conn.create(
            table if id is None else SurrealRecordID(table, id),
            document.model_dump(by_alias=True),
        )
        if isinstance(res, list):
            raise RuntimeError(f"Unexpected result from DB: {res}")
        return type(document).model_validate(res)

    def _insert_embedded(
        self,
        document: GenericDocument,
        id: int | str | None = None,
        table: str | None = None,
    ) -> GenericDocument:
        if not table:
            table = self._vector_table
        data_dict = document.model_dump()
        res = self.sync_conn.create(
            table if id is None else SurrealRecordID(table, id), data_dict
        )
        if isinstance(res, list):
            raise RuntimeError(f"Unexpected result from DB: {res}")
        try:
            return type(document).model_validate(res, by_alias=True)
        except Exception as e:
            logger.debug(f"Error while validating document: {e}")
            raise

    def embed_and_insert(
        self, doc: GenericDocument, table: str | None = None
    ) -> GenericDocument:
        if self.embedder is None:
            raise ValueError("Embedder is not initialized")
        if not table:
            table = self._vector_table
        if doc.content:
            embedding = self.embedder.embed(doc.content)
            doc.embedding = embedding
            return self._insert_embedded(doc, None, table)
        else:
            return self.insert_document(doc, None, table)

    def vector_search_from_text(
        self,
        doc_type: type[GenericDocument],
        text: str,
        *,
        table: str,
        k: int,
        score_threshold: float = -1,
        effort: int | None = 40,
    ) -> tuple[list[tuple[GenericDocument, float]], float]:
        if self.embedder is None:
            raise ValueError("Embedder is not initialized")
        embedding = self.embedder.embed(text)
        res, time = self.execute(
            "vector_search.surql",
            {"embedding": embedding, "threshold": score_threshold},
            {
                "table": table,
                "k": k,
                "effort_param": f",{effort}" if effort is not None else "",
            },
        )
        assert isinstance(res, list), f"Expected list, got {type(res)}: {res}"
        return [
            (doc_type.model_validate(record), record.get("score", 0))
            for record in res
        ], time

    def vector_search(
        self,
        doc_type: type[GenericDocument],
        query_embeddings: list[float],
        *,
        table: str | None = None,
        k: int = 5,
        effort: None = None,
        threshold: float = 0,
    ) -> tuple[list[tuple[GenericDocument, float]], float]:
        res, time = self.execute(
            "vector_search.surql",
            {
                "embedding": query_embeddings,
                "threshold": threshold,
            },
            {
                "k": k,
                "table": table if table is not None else self._vector_table,
                "effort_param": f",{effort}" if effort else "",
            },
        )
        if not isinstance(res, list):
            raise RuntimeError(f"Unexpected result from DB: {res}")
        return [
            (doc_type.model_validate(record), record.get("score", 0))
            for record in res
        ], time

    async def async_vector_search(
        self,
        doc_type: type[GenericDocument],
        query_embeddings: list[float],
        *,
        table: str | None = None,
        k: int = 5,
        effort: None = None,
        threshold: float = 0,
    ) -> tuple[list[tuple[GenericDocument, float]], float]:
        res, time = await self.async_execute(
            "vector_search.surql",
            {
                "embedding": query_embeddings,
                "threshold": threshold,
            },
            {
                "k": k,
                "table": table if table is not None else self._vector_table,
                "effort_param": f",{effort}" if effort else "",
            },
        )
        if not isinstance(res, list):
            raise RuntimeError(f"Unexpected result from DB: {res}")
        return [
            (doc_type.model_validate(record), record.get("score", 0))
            for record in res
        ], time

    # ==========================================================================
    # Graph
    # ==========================================================================

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
                _ = self.sync_conn.upsert(
                    SurrealRecordID(dest_table, dest.content), node
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
        if self.embedder is None:
            raise ValueError("Embedder is not initialized")
        node_destinations = [
            Node(dest, self.embedder.embed(dest))
            for dest in destinations
            if dest
        ]
        return self._add_graph_nodes(
            src_table,
            dest_table,
            node_destinations,
            edge_name,
            relations,
        )

    def recursive_graph_query(
        self,
        doc_type: type[GenericDocument],
        id: RecordID,
        rel: str,
        levels: int = 5,
    ) -> list[RecursiveResult[GenericDocument]]:
        rels = ", ".join(
            [
                f"@.{{{i}}}(->{rel}->?) AS bucket{i}"
                for i in range(1, levels + 1)
            ]
        )
        query = f"SELECT *, {rels} FROM $record"
        res = self.sync_conn.query(query, {"record": id})
        if not isinstance(res, list):
            raise RuntimeError(f"Unexpected result from DB: {res} with {query}")
        results: list[RecursiveResult[GenericDocument]] = []
        for item in res:
            buckets: list[RecordID] = []
            for i in range(1, levels + 1):
                bucket: RecordID | None = item.get(f"bucket{i}")
                if bucket is not None:
                    buckets = buckets + bucket
            try:
                results.append(
                    RecursiveResult[GenericDocument](
                        buckets=buckets, inner=doc_type.model_validate(item)
                    )
                )
            except ValidationError as e:
                print(f"Validation error: {e}")
        return results

    def graph_query_inward(
        self,
        doc_type: type[GenericDocument],
        id: RecordID | list[RecordID],
        rel: str,
        src: str,
        embedding: list[float] | None,
    ) -> tuple[list[GenericDocument], float]:
        res, time = self.execute(
            "graph_query_in.surql",
            {"record": id, "embedding": embedding},
            {"relation": rel, "src": src},
        )
        if isinstance(res, list):
            return list(map(lambda x: doc_type.model_validate(x), res)), time
        raise ValueError(f"Unexpected result from DB: {res}")

    def graph_siblings(
        self,
        doc_type: type[GenericDocument],
        id: RecordID,
        relation: str,
        src: str,
        dest: str,
    ) -> tuple[list[GenericDocument], float]:
        res, time = self.execute(
            "graph_siblings.surql",
            {"record": id},
            {
                "relation": relation,
                "src": src,
                "dest": dest,
            },
        )
        if isinstance(res, list):
            return list(map(lambda x: doc_type.model_validate(x), res)), time
        raise ValueError(f"Unexpected result from DB: {res}")
