import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import logfire
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from surrealdb import Value

from kaig.db import DB
from kaig.db.utils import query

from .db import init_db

logger = logging.getLogger(__name__)
stdout = logging.StreamHandler(stream=sys.stdout)
stdout.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(stdout)


surql_path = (
    Path(__file__).parent.parent.parent / "surql" / "search_chunks.surql"
)
with open(surql_path, "r") as file:
    search_surql = file.read()


@dataclass
class Deps:
    db: DB
    openai: AsyncOpenAI


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
    best_chunk_score: float
    chunks: list[ResultChunk]
    summary: str


agent = Agent(
    "openai:gpt-5-mini-2025-08-07",
    deps_type=Deps,
    instructions="""
        Base your answers on the user's knowledge base, and include
        the document name in the answer. Do not ask follow up questions.
    """,
)


@agent.tool
async def retrieve(context: RunContext[Deps], search_query: str) -> str:
    """Retrieve documents from the user's knowledge base based on a search query.

    Args:
        context: The call context.
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


openai = AsyncOpenAI()

_ = logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()
logfire.instrument_surrealdb()
_ = logfire.instrument_openai(openai)

db = init_db(init_llm=False, init_indexes=False)

# Agent chat UI
app = agent.to_web(deps=Deps(db, openai))
