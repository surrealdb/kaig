from pathlib import Path

import logfire
from pydantic_ai import FunctionToolset, RunContext, Tool
from tools.deps import Deps

from kaig.definitions import SurrealRawResponse

# TODO: generate dynamically using `INFO FOR` and looping through tables and fields
SCHEMA = r"""
-- TABLE: REL_PRODUCT_IN_ORDER
DEFINE TABLE REL_PRODUCT_IN_ORDER TYPE RELATION IN product OUT order SCHEMAFULL;

DEFINE FIELD in ON REL_PRODUCT_IN_ORDER TYPE record<product>;
DEFINE FIELD out ON REL_PRODUCT_IN_ORDER TYPE record<order>;
DEFINE FIELD qty ON REL_PRODUCT_IN_ORDER TYPE number;

-- TABLE: category
DEFINE TABLE category TYPE NORMAL SCHEMAFULL;

DEFINE FIELD embedding ON category TYPE array<float> | none;
DEFINE FIELD embedding.* ON category TYPE float;
DEFINE FIELD flow_embedded ON category TYPE string | none;
DEFINE FIELD name ON category TYPE string;
DEFINE FIELD parent ON category TYPE record<category> | none;

-- TABLE: order
DEFINE TABLE order TYPE NORMAL SCHEMAFULL;

DEFINE FIELD created_at ON order TYPE datetime READONLY VALUE time::now();
DEFINE FIELD user ON order TYPE record<user>;

-- TABLE: product
DEFINE TABLE product TYPE NORMAL SCHEMAFULL;

DEFINE FIELD category ON product TYPE record<category>;
DEFINE FIELD description ON product TYPE string;
DEFINE FIELD embedding ON product TYPE array<float> | none;
DEFINE FIELD embedding.* ON product TYPE float;
DEFINE FIELD flow_embedded ON product TYPE string | none;
DEFINE FIELD name ON product TYPE string;
DEFINE FIELD price ON product TYPE float;

-- TABLE: review
DEFINE TABLE review TYPE NORMAL SCHEMAFULL;

DEFINE FIELD created_at ON  review TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD embedding ON review TYPE array<float> | none;
DEFINE FIELD embedding.* ON review TYPE float;
DEFINE FIELD flow_sentiment ON review TYPE string | none;
DEFINE FIELD product ON review TYPE record<product>;
DEFINE FIELD score ON review TYPE float;
DEFINE FIELD sentiment ON review TYPE string | none;
DEFINE FIELD text ON review TYPE string;
DEFINE FIELD user ON review TYPE record<user>;

-- TABLE: user
DEFINE TABLE user TYPE NORMAL SCHEMAFULL;

DEFINE FIELD created_at ON user TYPE datetime READONLY VALUE time::now();
DEFINE FIELD deleted_at ON user TYPE none | datetime DEFAULT NONE;
DEFINE FIELD display_name ON user TYPE none | string;
DEFINE FIELD email ON user TYPE string ASSERT string::is_email($value);
DEFINE FIELD name ON user TYPE string | none;
DEFINE FIELD password_hash ON user TYPE string;
DEFINE FIELD role ON user TYPE string ASSERT $value INSIDE ['user', 'admin'];
DEFINE FIELD updated_at ON user TYPE datetime VALUE time::now();
"""

NOTES = """
- use vector search when searching for categories, products, and reviews.
- vector search threshold recommended: 0.20
"""

# read examples from a file
with open(Path(__file__).parent / "examples/query_db.surql", "r") as f:
    examples = f.read()


async def query_db(context: RunContext[Deps], question: str) -> str:
    """Use this tool to answer questions about products, orders, reviews, or users.

    If required, you can do vector search against any table with an embeddings field. E.g: `WHERE embedding <|20,40|> fn::embed("text to embed")`.

    Args:
        question: The user question.
    """
    db = context.deps.db
    if db.llm is None:
        raise ValueError("LLM not available")

    with logfire.span("Generating query for {question=}", question=question):
        surql_query = db.llm.gen_surql(question, SCHEMA, examples, NOTES)
        results = db.sync_conn.query_raw(surql_query, {})

    # -- Build result string and calculate success rate of queries
    response = SurrealRawResponse.model_validate(results)
    if response.error:
        oks = [0]
        result = response.error.message
    else:
        items = response.result or []
        oks = [1 if item.status == "OK" else 0 for item in items]
        parsed_results = [item.result for item in items]  # pyright: ignore[reportAny]
        result = (
            str(parsed_results[0])  # pyright: ignore[reportAny]
            if len(parsed_results) == 1
            else str(parsed_results)
        )

    # store query and success rate in analytics table
    db.insert_analytics_data(
        "query_ecomm", surql_query, str(results), sum(oks) / len(oks), "1"
    )

    return result


def build_query_db_toolset() -> FunctionToolset[Deps]:
    tools = [
        Tool(query_db, takes_ctx=True),
    ]
    return FunctionToolset(tools)
