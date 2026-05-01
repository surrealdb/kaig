from dataclasses import dataclass
from pathlib import Path
from typing import cast

import logfire
from pydantic_ai import RunContext
from surrealdb import Value
from tools.deps import Deps

from kaig.db.utils import query

# SurQL files
surql_path = (
    Path(__file__).parent.parent / "surql" / "search_chunks.surql"
    # Path(__file__).parent / "surql" / "search_concepts.surql"
)
with open(surql_path, "r") as file:
    search_surql = file.read()


@dataclass
class ResultChunk:
    id: str
    score: float
    chunk_index: int
    content: str


@dataclass
class DocHandle:
    id: str
    filename: str
    content_type: str


@dataclass
class SearchResult:
    doc: DocHandle
    best_score: float
    chunks: list[ResultChunk]


async def similarity(context: RunContext[Deps], search_query: str) -> str:
    """Retrieve documents from the knowledge base using similarity search.

    Args:
        search_query: The search query.
    """
    db = context.deps.db

    with logfire.span(
        "vector+graph search for {search_query=}", search_query=search_query
    ):
        if db.embedder is None:
            raise ValueError("Embedder is not configured")

        embedding = db.embedder.embed(search_query)
        results = query(
            db.sync_conn,
            search_surql,
            {"embedding": cast(Value, embedding), "threshold": 0.4},
            SearchResult,
        )

    results = "\n\n".join(
        f"# Document name: {x.doc.filename}\n{'\n\n'.join(str(y.content) for y in x.chunks)}\n"
        for x in results
    )
    # logger.debug("Retrieved data: %s", results)
    return results
