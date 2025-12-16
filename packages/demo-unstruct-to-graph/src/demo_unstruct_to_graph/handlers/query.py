import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import logfire
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from surrealdb import Value

from demo_unstruct_to_graph.db import init_db
from kaig.db import DB
from kaig.db.utils import query

logger = logging.getLogger(__name__)
stdout = logging.StreamHandler(stream=sys.stdout)
stdout.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(stdout)


surql_path = Path(__file__).parent.parent / "surql" / "search.surql"
with open(surql_path, "r") as file:
    q = file.read()


@dataclass
class Deps:
    db: DB
    openai: AsyncOpenAI


# @dataclass
# class ResultChunk:
#     chunk: str
#     score: float
#     chunk_index: int
#     content: str


@dataclass
class SearchResult:
    doc: str
    best_chunk_score: float
    # chunks: list[ResultChunk]
    chunks: list[dict[str, str | float | int]]


MODEL = "openai:gpt-5-mini-2025-08-07"
agent = Agent(MODEL, deps_type=Deps)


@agent.tool
async def retrieve(context: RunContext[Deps], search_query: str) -> str:
    """Retrieve document sections based on a search query.

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
            q,
            {"embedding": cast(Value, embedding), "threshold": 0.2},
            SearchResult,
        )

    results = "\n\n".join(
        f"# Document {x.doc} ({x.best_chunk_score:.2f})\n{'\n\n'.join(str(y['content']) for y in x.chunks)}\n"
        for x in results
    )
    logger.debug("Retrieved data: %s", results)
    return results


async def query_handler(db: DB, question: str) -> str:
    openai = AsyncOpenAI()
    _ = logfire.instrument_openai(openai)

    logfire.info('Asking "{question}"', question=question)

    deps = Deps(db=db, openai=openai)
    answer = await agent.run(question, deps=deps)

    return answer.output


if __name__ == "__main__":
    import asyncio
    import sys

    _ = logfire.configure(send_to_logfire="if-token-present")
    logfire.instrument_pydantic_ai()
    logfire.instrument_surrealdb()

    question = sys.argv[1]
    print(f"question: {question}")

    db = init_db(init_llm=False, init_indexes=False)

    res = asyncio.run(query_handler(db, question))

    print(f"result: {res}")
