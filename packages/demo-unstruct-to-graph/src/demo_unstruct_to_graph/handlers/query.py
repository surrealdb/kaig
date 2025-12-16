import logging
import sys
from dataclasses import dataclass

import logfire
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext

from demo_unstruct_to_graph.db import init_db
from demo_unstruct_to_graph.definitions import Chunk
from kaig.db import DB

logger = logging.getLogger(__name__)
stdout = logging.StreamHandler(stream=sys.stdout)
stdout.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(stdout)


@dataclass
class Deps:
    db: DB
    openai: AsyncOpenAI


MODEL = "openai:gpt-5-mini-2025-08-07"
agent = Agent(MODEL, deps_type=Deps)


@agent.tool
async def retrieve(context: RunContext[Deps], search_query: str) -> str:
    """Retrieve document sections based on a search query.

    Args:
        context: The call context.
        search_query: The search query.
    """
    with logfire.span(
        "vector search for {search_query=}", search_query=search_query
    ):
        chunks, _time = context.deps.db.vector_search_from_text(
            Chunk, search_query, table="chunk", k=5
        )
        # TODO: get documents related to chunks

    results = "\n\n".join(
        f"# Chunk {chunk.id} ({score:.2f})\n{chunk.content}\n"
        for chunk, score in chunks
    )
    logger.debug("Retrieved chunks: %s", results)
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
    # TODO: uncomment this
    # logfire.instrument_surrealdb()

    query = sys.argv[1]
    print(f"query: {query}")

    db = init_db(init_llm=False, init_indexes=False)

    res = asyncio.run(query_handler(db, query))

    print(f"result: {res}")
