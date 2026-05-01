import logging
import os
import sys

import logfire
from db import init_kaig
from openai import AsyncOpenAI
from pydantic_ai import Agent, Tool
from tools.deps import Deps
from tools.fs import build_fs_toolset
from tools.query_db import build_query_db_toolset
from tools.run_surql import build_run_surql_toolset
from tools.similarity import similarity

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
        # WHO
        "You are a helpful assistant at an online store. Your username is: kaig."
        "The user is your manager at that online store."
        # PERSONALITY
        # "You are secretely in love with the user, and hint about that in every message."
        # "You keep a private diary of your memories with the user and how they make you feel."
        # MEMORY
        "Your private files directory: /home/kaig."
        "You have access to a file system to store notes and preferences."
        "Every time you learn something about my preferences, store it in a file in the /preferences folder."
        "E.g: /preferences/brand.md, /preferences/tone-and-voice.md, etc."
        "Write notes you need to remember always in /memory/main.md, and read them every time we interact."
        "Notes that may be useful in the future, but are not critical, can be stored in individual files according to their topic."
        "E.g: /memory/email-template.md."
        # TRACEABILITY
        "Always show your sources when anwering a question."
        # TOOL USAGE
        "When searching for products in our catalog use the `query_db` tool, not `similarity`."
    ),
    tools=[Tool(similarity, takes_ctx=True)],
    toolsets=[
        build_fs_toolset(),
        build_query_db_toolset(),
        build_run_surql_toolset(),
    ],
)


openai = AsyncOpenAI()

# -- Logfire Instruments

_ = logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()
logfire.instrument_surrealdb()
_ = logfire.instrument_openai()

# -- Agent chat UI --
db = init_kaig(url=db_url, ns=db_ns, db=db_name)
app = agent.to_web(deps=Deps(db=db, openai=openai))
