from typing import Any

from langchain_community.graphs.graph_document import GraphDocument, Node
from langchain_community.graphs.graph_store import GraphStore
from surrealdb import (
    AsyncHttpSurrealConnection,
    AsyncWsSurrealConnection,
    BlockingHttpSurrealConnection,
    BlockingWsSurrealConnection,
    RecordID,
)

SurrealConnection = BlockingWsSurrealConnection | BlockingHttpSurrealConnection
SurrealAsyncConnection = AsyncWsSurrealConnection | AsyncHttpSurrealConnection

CREATE_SOURCE_QUERY = """
    CREATE type::table($table)
    CONTENT $content
"""

CREATE_NODE_QUERY = """
    CREATE $record_id
    CONTENT $content
"""

RELATE_QUERY = """
    RELATE $in->(type::table($relation))->$out
    CONTENT $content
"""


class SurrealDBGraph(GraphStore):
    def __init__(
        self,
        connection: SurrealConnection,
        *,
        table_prefix: str = "graph_",
    ) -> None:
        self.connection = connection
        self.table_prefix = table_prefix

    def _query(self, surql: str, vars: dict) -> dict:
        return self.connection.query_raw(surql, vars)

    def _build_node_recordid(self, node: Node) -> RecordID:
        return RecordID(self.table_prefix + node.type, node.id)

    @property
    def get_schema(self) -> str:
        """Return the schema of the Graph database"""
        raise NotImplementedError

    @property
    def get_structured_schema(self) -> dict[str, Any]:
        """Return the schema of the Graph database"""
        raise NotImplementedError

    def query(self, query: str, params: dict = {}) -> list[dict[str, Any]]:
        """Query the graph."""
        raise NotImplementedError

    def refresh_schema(self) -> None:
        """Refresh the graph schema information."""
        raise NotImplementedError

    def add_graph_documents(
        self, graph_documents: list[GraphDocument], include_source: bool = False
    ) -> None:
        """Take GraphDocument as input and uses it to construct a graph."""
        for doc in graph_documents:
            source = None
            if include_source:
                source = self._query(
                    CREATE_SOURCE_QUERY,
                    {
                        "table": self.table_prefix + "source",
                        "content": {
                            "page_content": doc.source.page_content,
                            "metadata": doc.source.metadata,
                        },
                    },
                )
                source = source["result"][0]["result"][0]

            for node in doc.nodes:
                self._query(
                    CREATE_NODE_QUERY,
                    {
                        "record_id": self._build_node_recordid(node),
                        "content": node.properties,
                    },
                )
                if include_source:
                    self._query(
                        RELATE_QUERY,
                        {
                            "in": source["id"],
                            "relation": "MENTIONS",
                            "out": self._build_node_recordid(node),
                            "content": {},
                        },
                    )

            for rel in doc.relationships:
                self._query(
                    RELATE_QUERY,
                    {
                        "in": self._build_node_recordid(rel.source),
                        "relation": rel.type,
                        "out": self._build_node_recordid(rel.target),
                        "content": rel.properties,
                    },
                )
