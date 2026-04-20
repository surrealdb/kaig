import logging
import os
import sys

import logfire
from db import init_kaig
from openai import AsyncOpenAI
from pydantic_ai import Agent, Tool
from tools.deps import Deps
from tools.docs import retrieve
from tools.ecomm import build_ecomm_toolset
from tools.fs import build_fs_toolset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
stdout = logging.StreamHandler(stream=sys.stdout)
stdout.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(stdout)

db_url = os.environ.get("SURREALDB_URL", "ws://localhost:8000")
db_ns = os.environ.get("SURREALDB_NAMESPACE", "test")
db_name = os.environ.get("SURREALDB_DATABASE", "test")


agent = Agent(
    "openai:gpt-5-mini-2025-08-07",
    deps_type=Deps,
    instructions=(
        "You are a helpful assistant that organizes my thoughts, conversations, notes, into a well-structured text file system."
        "Every time you learn something about my preferences, store it in a file in the /preferences folder. For example, create files like /preferences/food.md, /preferences/music.md, /preferences/books.md, etc."
        # "When I talk about a project or task, organize the notes and current to-do list in a /project/<project_name> folder. For example, /project/social_media/2026/post_calendar_january.md or /project/support/solutions/vector_index.md"
        "Write your main notes in /notes.md, and read them every time we interact."
        "Before you answer, consider updating the /notes.md file with your latest thoughts and insights."
        "Use the `query_ecomm` tool to answer questions about products, orders, reviews, or users."
        "For information about the products (characteristics, troubleshooting, etc) answers based on retrieved documents using the `retrieve` tool, keep your answers concise, and include the document name in the answer."
    ),
    tools=[Tool(retrieve, takes_ctx=True)],
    toolsets=[build_fs_toolset(), build_ecomm_toolset()],
)


openai = AsyncOpenAI()

_ = logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()
logfire.instrument_surrealdb()
_ = logfire.instrument_openai(openai)


db = init_kaig(url=db_url, ns=db_ns, db=db_name)

# Agent chat UI
app = agent.to_web(deps=Deps(db=db, openai=openai))
