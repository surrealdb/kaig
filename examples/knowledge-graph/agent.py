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
        "You are a helpful assistant with access to a file system to store notes and preferences."
        "Every time you learn something about my preferences, store it in a file in the /preferences folder. For example, create files like /preferences/brand.md, /preferences/tone-and-voice.md, etc."
        "Write notes you need to remember always in /memory/main.md, and read them every time we interact."
        "Notes that may be useful in the future, but are not critical, can be stored in individual files according to their topic. For example, /memory/email-template.md."
        "Use the `query_ecomm` tool to run queries against the database (read and write)."
        "Use the `retrieve` tool to search in files, documents, and memories. Include the document name in the answer."
    ),
    tools=[Tool(retrieve, takes_ctx=True)],
    toolsets=[build_fs_toolset(), build_ecomm_toolset()],
)


openai = AsyncOpenAI()

# -- Logfire Instruments

_ = logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()
logfire.instrument_surrealdb()
_ = logfire.instrument_openai(openai)

# -- Agent chat UI --
db = init_kaig(url=db_url, ns=db_ns, db=db_name)
app = agent.to_web(deps=Deps(db=db, openai=openai))
