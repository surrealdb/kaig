import hashlib
import logging
import sys
from dataclasses import asdict
from pathlib import Path
from textwrap import dedent
from typing import Any, cast

import logfire
from pydantic import BaseModel, ValidationError
from surrealdb import (
    AsyncHttpSurrealConnection,
    AsyncSurreal,
    AsyncWsSurrealConnection,
    BlockingHttpSurrealConnection,
    BlockingWsSurrealConnection,
    RecordID,
    Surreal,
    Value,
)
from surrealdb import (
    RecordID as SurrealRecordID,
)

from ..definitions import (
    Analytics,
    GenericDocument,
    Node,
    Object,
    OriginalDocument,
    RecursiveResult,
    Relation,
    Relations,
    VectorTableDefinition,
)
from ..embeddings import Embedder
from ..llm import LLM
from . import utils
from .queries import COUNT_QUERY

logger = logging.getLogger(__name__)

_ = logfire.configure(send_to_logfire="if-token-present")


class DB:
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        namespace: str,
        database: str,
        embedder: Embedder | None = None,
        llm: LLM | None = None,
        *,
        analytics_table: str = "analytics",
        original_docs_table: str = "document",
        tables: list[str] | None = None,
        vector_tables: list[VectorTableDefinition] | None = None,
        graph_relations: list[Relation] | None = None,
    ):
        logfire.instrument_surrealdb()

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
        self._original_docs_table: str = original_docs_table
        self._analytics_table: str = analytics_table
        self._tables: list[str] = tables or []
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

    def init_db(self, force: bool = False) -> None:
        r"""This needs to be called to initialise the DB indexes.
        Only required if you defined `vector_tables` or `graph_relations`.
        """

        if not force:
            # Check if the database is already initialized
            is_init = self.sync_conn.query(
                "SELECT * FROM ONLY meta:initialized"
            )
            # query return type is wrong, in this case it could return None
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

        # -- original documents table
        _ = self.execute(
            "define_table.surql",
            None,
            {
                "name": self._original_docs_table,
                "fields": dedent(f"""
                    DEFINE FIELD OVERWRITE filename ON {self._original_docs_table} TYPE string;
                    DEFINE FIELD OVERWRITE file ON {self._original_docs_table} TYPE bytes;
                """),
            },
        )

        # -- analytics table
        _ = self.execute(
            "define_table.surql",
            None,
            {
                "name": self._analytics_table,
                "fields": dedent(f"""
                    DEFINE FIELD OVERWRITE input ON {self._analytics_table} TYPE string;
                    DEFINE FIELD OVERWRITE output ON {self._analytics_table} TYPE string;
                    DEFINE FIELD OVERWRITE key ON {self._analytics_table} TYPE string;
                    DEFINE FIELD OVERWRITE score ON {self._analytics_table} TYPE float;
                """),
            },
        )

        _ = self.sync_conn.upsert("meta:initialized")
        logger.info("Database initialized")

    def clear(self) -> None:
        res = self.sync_conn.query("REMOVE TABLE IF EXISTS meta;")
        res = self.sync_conn.query(
            f"REMOVE TABLE IF EXISTS {self._analytics_table};"
        )
        logger.debug(res)
        for table in self._tables:
            res = self.sync_conn.query(f"REMOVE TABLE IF EXISTS {table};")
            logger.debug(res)
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

    @property
    def original_docs_table(self) -> str:
        return self._original_docs_table

    # ==========================================================================
    # Connections
    # ==========================================================================

    @property
    async def async_conn(
        self,
    ) -> AsyncWsSurrealConnection | AsyncHttpSurrealConnection:
        if self._async_conn is None:
            self._async_conn = AsyncSurreal(self.url)
            if self.url != "mem://":
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
            if self.url != "mem://":
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

    def _extract_result_and_time(self, res: Object) -> tuple[Value, float]:
        if "result" in res:
            result = res["result"]
            if result is not None and isinstance(result, list):
                result_inner = result[0]
                if isinstance(result_inner, dict):
                    obj = result_inner["result"]
                    time = str(result_inner["time"])
                    return obj, utils.parse_time(time)
        raise ValueError(f"unexpected result: {res}")

    def execute(
        self,
        file: str | Path,
        vars: Object | None = None,
        template_vars: Object | None = None,
    ) -> tuple[Value, float]:
        surql = self._load_surql(file)
        if template_vars is not None:
            surql = surql.format(**template_vars)
        res: Object = self.sync_conn.query_raw(
            surql, cast(dict[str, Value], vars)
        )
        return self._extract_result_and_time(res)

    async def async_execute(
        self,
        file: str | Path,
        vars: dict[str, Value] | None = None,
        template_vars: Object | None = None,
    ) -> tuple[Value, float]:
        surql = self._load_surql(file)
        if template_vars is not None:
            surql = surql.format(**template_vars)
        conn = await self.async_conn
        res: Object = await conn.query_raw(surql, vars)
        return self._extract_result_and_time(res)

    # ==========================================================================
    # Basic queries
    # ==========================================================================

    def query(
        self,
        query: str,
        vars: Object,
        record_type: type[utils.RecordType],
    ) -> list[utils.RecordType]:
        r'''Query a list of records and assert their expected type `record_type`

        Args:
            query (str): The query to execute.
            vars (Object): The variables to use in the query.
            record_type (type[utils.RecordType]): The expected type of the records.

        Returns:
            list[utils.RecordType]: The list of records.

        Raises:
            TypeError: If the records are not of the expected type.

        Example:
        ```python
        from kaig.db.queries import WhereClause, order_limit_start
        from surrealdb import RecordID

        where = WhereClause()
        where = where.and_("team", RecordID("team", "green"))
        where_clause, where_vars = where.build()
        order_limit_start_clause = order_limit_start("username", "DESC", 5, 0)
        query = dedent(f"""
            SELECT *
            FROM user
            {where_clause}
            {order_limit_start_clause}
        """)
        filtered = db.query(query, where_vars, User)
        ```
        '''
        return utils.query(self.sync_conn, query, vars, record_type)

    def query_one(
        self,
        query: str,
        vars: Object,
        record_type: type[utils.RecordType],
    ) -> utils.RecordType | None:
        return utils.query_one(self.sync_conn, query, vars, record_type)

    def count(
        self,
        table: str,
        where_clause: str,
        where_vars: Object,
        group_by: str | None = None,
    ) -> int:
        total_count_query = COUNT_QUERY.format(
            table=table,
            where_clause=where_clause,
            group_clause="GROUP ALL"
            if group_by is None
            else f"GROUP BY{group_by}",
        )
        count_result = self.query_one(
            total_count_query, where_vars, dict[str, int]
        )
        total_count = count_result.get("count") if count_result else 0
        assert isinstance(total_count, int), (
            f"Expected int, got {type(total_count)}"
        )
        total_count = int(total_count)
        return total_count

    def exists(self, record: SurrealRecordID) -> bool:
        exists = self.sync_conn.query(
            "RETURN record::exists($record)",
            {"record": record},
        )
        # query return type is wrong, in this case it could return a bool
        if not isinstance(exists, bool):
            return False
        return exists

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

    # TODO: fix if surrealdb.py changes the type for the RecordID identifier
    async def error_exists(self, id: Any) -> bool:  # pyright: ignore[reportExplicitAny, reportAny]
        conn = await self.async_conn
        res = await conn.query(
            "RETURN record::exists($record)",
            {"record": SurrealRecordID("error", id)},
        )
        # query return type is wrong, in this case it could return a bool
        if not isinstance(res, bool):
            raise RuntimeError(
                f"Unexpected result from error_exists: {type(res)}"
            )
        return res

    # ==========================================================================
    # Original Documents
    # ==========================================================================

    def store_original_document(
        self, file: str, content_type: str
    ) -> tuple[OriginalDocument, bool]:
        """Returns a tuple of the document and a bool indicating whether the
        document was chached (True) or inserted (False)"""

        source = Path(file)

        # TODO: store files as files instead of bytes
        #       https://surrealdb.com/docs/surrealql/datamodel/files
        file_content = bytes()

        with open(source, "rb") as f:
            md5_hash = hashlib.md5()
            while True:
                c = f.read(4096)
                if not c:
                    break
                md5_hash.update(c)
                file_content += c
            doc_hash = md5_hash.hexdigest()

        return self.store_original_document_from_bytes(
            source.name, content_type, file_content, doc_hash
        )

    def store_original_document_from_bytes(
        self,
        filename: str,
        content_type: str,
        file_bytes: bytes,
        precomputed_hash: str | None = None,
    ) -> tuple[OriginalDocument, bool]:
        """Returns a tuple of the document and a bool indicating whether the
        document was chached (True) or inserted (False)"""

        md5_hash = hashlib.md5()
        md5_hash.update(file_bytes)
        hex_hash = md5_hash.hexdigest()

        if precomputed_hash is not None and hex_hash != precomputed_hash:
            logger.warning(
                f"Hash mismatch for {filename}: {hex_hash} != {precomputed_hash}"
            )

        # -- check if the document already exists
        record_id = SurrealRecordID(self._original_docs_table, hex_hash)
        cached = self.query_one(
            "SELECT * FROM ONLY $record",
            {"record": record_id},
            OriginalDocument,
        )
        if cached:
            # update the document to trigger process
            _ = self.query_one(
                "UPDATE ONLY $record", {"record": record_id}, Object
            )
            return cached, True
        else:
            content = OriginalDocument(
                record_id, filename, content_type, file_bytes, None
            )
            inserted = self.query_one(
                "CREATE ONLY $record CONTENT $content",
                {"record": record_id, "content": asdict(content)},
                OriginalDocument,
            )
            if not inserted:
                raise Exception(
                    "Failed to create document: CREATE returned NONE."
                )
            return inserted, False

    # ==========================================================================
    # Documents (or more precisely: chunks)
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
            raise RuntimeError(
                f"Unexpected result from get_documents: {type(res)}"
            )
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
            raise RuntimeError(
                f"Unexpected result from list_documents: {type(res)}"
            )
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

    # TODO: should we merge insert_document and _insert_embedded together?
    def insert_document(
        self,
        document: GenericDocument,
        id: int | str | None = None,
        table: str | None = None,
    ) -> GenericDocument:
        if not table:
            table = self._vector_table
        data_dict = document.model_dump(by_alias=True)
        if id is not None and data_dict["id"]:
            del data_dict["id"]
        res = self.sync_conn.create(
            table if id is None else SurrealRecordID(table, id), data_dict
        )
        if isinstance(res, list):
            raise RuntimeError(f"Unexpected result from insert_document: {res}")
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
        if id is not None and data_dict["id"]:
            del data_dict["id"]
        res = self.sync_conn.create(
            table if id is None else SurrealRecordID(table, id), data_dict
        )
        if isinstance(res, list):
            raise RuntimeError(
                f"Unexpected result from _inserted_embedded: {res} with {table}:{id}"
            )
        try:
            return type(document).model_validate(res, by_alias=True)
        except Exception as e:
            logger.debug(f"Error while validating document: {e}")
            raise

    def embed_and_insert(
        self,
        doc: GenericDocument,
        table: str | None = None,
        id: int | str | None = None,
        force: bool = False,
    ) -> GenericDocument:
        if self.embedder is None:
            raise ValueError("Embedder is not initialized")
        if not table:
            table = self._vector_table
        rec_id = SurrealRecordID(table, id)
        with logfire.span("Embed and insert {rec_id=}", rec_id=rec_id):
            if id is not None and not force:
                existing = self.query_one(
                    "SELECT * FROM ONLY $record",
                    {"record": rec_id},
                    type(doc),
                )
                if existing:
                    return existing
            if doc.content:
                content = doc.content
                while True:
                    try:
                        embedding = self.embedder.embed(content)
                        break
                    except Exception as e:
                        # do we need to truncate the chunk to embed it?
                        if "the input length exceeds the context length" in str(
                            e
                        ):
                            # retry
                            content = content[: self.embedder.max_length]
                            logger.info("Retry embedding chunk")
                            continue
                        logger.error(
                            f"Error embedding doc with len={len(content)}: {type(e)} {e}"
                        )
                        raise e

                doc.embedding = embedding
                return self._insert_embedded(doc, id, table)
            else:
                return self.insert_document(doc, id, table)

    def _extract_similarity_results(
        self, res: Value, doc_type: type[GenericDocument]
    ) -> list[tuple[GenericDocument, float]]:
        if not isinstance(res, list):
            raise RuntimeError(f"Unexpected result from vector search: {res}")
        results: list[tuple[GenericDocument, float]] = []
        for record in res:
            if isinstance(record, dict):
                score = cast(float, record.get("score", 0))
            else:
                score = 0
            if isinstance(record, dict):
                results.append((doc_type.model_validate(record), score))
        return results

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
            {
                "embedding": cast(list[Value], embedding),
                "threshold": score_threshold,
            },
            {
                "table": table,
                "k": k,
                "effort_param": f",{effort}" if effort is not None else "",
            },
        )
        return self._extract_similarity_results(res, doc_type), time

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
                "embedding": cast(list[Value], query_embeddings),
                "threshold": threshold,
            },
            {
                "k": k,
                "table": table if table is not None else self._vector_table,
                "effort_param": f",{effort}" if effort else "",
            },
        )
        return self._extract_similarity_results(res, doc_type), time

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
                "embedding": cast(list[Value], query_embeddings),
                "threshold": threshold,
            },
            {
                "k": k,
                "table": table if table is not None else self._vector_table,
                "effort_param": f",{effort}" if effort else "",
            },
        )
        return self._extract_similarity_results(res, doc_type), time

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
            raise RuntimeError(
                f"Unexpected result from recursive_graph_query: {res} with {query}"
            )
        results: list[RecursiveResult[GenericDocument]] = []
        for item in res:
            buckets: list[RecordID] = []
            for i in range(1, levels + 1):
                if isinstance(item, dict) and f"bucket{i}" in item:
                    bucket = item.get(f"bucket{i}")
                    if bucket is not None and isinstance(
                        bucket, SurrealRecordID
                    ):
                        buckets.append(bucket)
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
            {
                "record": cast(RecordID, id),
                "embedding": cast(list[Value], embedding),
            },
            {"relation": rel, "src": src},
        )
        if isinstance(res, list):
            return list(map(lambda x: doc_type.model_validate(x), res)), time
        raise ValueError(f"Unexpected result from graph_query_inward: {res}")

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
        raise ValueError(f"Unexpected result from graph_siblings: {res}")
