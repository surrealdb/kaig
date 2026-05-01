from pydantic_ai import FunctionToolset, RunContext, Tool
from tools.deps import Deps

from kaig.definitions import OriginalDocument, SurrealRawResponse


async def run_surql(context: RunContext[Deps], file_path: str) -> str:
    """
    Run a raw SurQL query against the database.

    Args:
        file_path (str): The path to the SurQL file to execute.
    """
    db = context.deps.db

    # modulirize, because it's duplicated code from fs/cat
    if not file_path.startswith("/"):
        file_path = "/" + file_path

    result = db.query_one(
        "SELECT * FROM ONLY file WHERE path = $path LIMIT 1",
        {"path": file_path},
        OriginalDocument,
    )
    if result is None:
        return f"File not found: {file_path}"
    surql = result.content or ""

    if db.llm is None:
        raise ValueError("LLM not available")

    results = db.sync_conn.query_raw(surql, {})

    # -- Build result string and calculate success rate of queries
    response = SurrealRawResponse.model_validate(results)
    if response.error:
        result = response.error.message
    else:
        items = response.result or []
        parsed_results = [item.result for item in items]  # pyright: ignore[reportAny]
        result = (
            str(parsed_results[0])  # pyright: ignore[reportAny]
            if len(parsed_results) == 1
            else str(parsed_results)
        )

    return result


def build_run_surql_toolset() -> FunctionToolset[Deps]:
    tools = [
        Tool(run_surql, takes_ctx=True),
    ]
    return FunctionToolset(tools)
