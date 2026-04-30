import logfire
from pydantic_ai import FunctionToolset, RunContext, Tool
from tools.deps import Deps

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


async def query_ecomm(context: RunContext[Deps], question: str) -> str:
    """Use this tool to answer questions about products, orders, reviews, or users.

    If required, you can do vector search against any table with an embeddings field. E.g: `WHERE embedding <|20,40|> fn::embed("text to embed")`.

    Args:
        question: The user question.
    """
    db = context.deps.db
    if db.llm is None:
        raise ValueError("LLM not available")

    with logfire.span("Generating query for {question=}", question=question):
        examples = [
            r"""-- example query: total product items sold
SELECT *,
    math::sum(->REL_PRODUCT_IN_ORDER.qty) AS total
OMIT embedding
FROM product;""",
            r"""-- example query: top product sales after date
SELECT
    in.{id,name} AS product,
    math::sum(qty) AS count
FROM REL_PRODUCT_IN_ORDER
WHERE out IN (
    SELECT VALUE id FROM order WHERE created_at > d'2026-04-09T12:00:00.0Z'
)
GROUP BY product
ORDER BY count DESC
LIMIT 10;""",
            r"""-- example query: top product sales extended with their reviews
LET $since = d'2026-03-07T12:00:00.0Z';
LET $best = SELECT
    in.{id,name} AS product,
    math::sum(qty) AS count
FROM REL_PRODUCT_IN_ORDER
WHERE out IN (
    SELECT VALUE id FROM order WHERE created_at > $since
)
GROUP BY product
ORDER BY count DESC
LIMIT 10;

// extend each product with its reviews since $since ordered by descending score
RETURN $best.map(|$x| $x + {
    reviews: (
        SELECT * FROM review
        WHERE product = $x.product.id AND created_at > $since
        ORDER BY score DESC
    )
});
""",
            r"""--- example query: top 5 customers
SELECT
    id AS customer_id,
    email,
    (SELECT VALUE math::sum(in.price * qty)
     FROM ONLY REL_PRODUCT_IN_ORDER
     WHERE out.user = $parent.id
     GROUP ALL
    ) AS total_spend,
    (SELECT VALUE math::sum(1) FROM ONLY order WHERE user = $parent.id GROUP ALL) AS order_count,
    (SELECT VALUE created_at FROM ONLY order WHERE user = $parent.id ORDER BY created_at DESC LIMIT 1) AS last_order_date
FROM user
ORDER BY total_spend DESC
LIMIT 5;
""",
            r"""--- example query: vector search with threshold
LET $vector = fn::embed("text to embed");
SELECT *, score
OMIT embedding
FROM (
    SELECT *, (1 - vector::distance::knn()) AS score
    FROM product
    WHERE embedding <|20, 40|> $vector
)
WHERE score >= $threshold
ORDER BY score DESC;
""",
        ]
        # schema = db.query_one("INFO FOR DB")
        surql_query = db.llm.gen_surql(question, SCHEMA, examples)
        logfire.debug(surql_query)
        results = db.sync_conn.query_raw(surql_query, {})

    # -- Build result string and calculate success rate of queries
    # TODO: turn results into a BaseModel so we can validate it
    oks: list[int] = []
    result = results.get("result", results)
    parsed_results = []
    if isinstance(result, list):
        for item in result:
            oks.append(1 if item.get("status", "ERROR") == "OK" else 0)
            parsed_results.append(item.get("result", item))
    else:
        oks.append(1 if result.get("status", "ERROR") == "OK" else 0)
        parsed_results.append(result)
    result = (
        str(parsed_results[0])
        if len(parsed_results) == 1
        else str(parsed_results)
    )

    # store query and success rate in analytics table
    db.insert_analytics_data(
        "query_ecomm", surql_query, str(results), sum(oks) / len(oks), "1"
    )

    return result


def build_ecomm_toolset() -> FunctionToolset[Deps]:
    tools = [
        Tool(query_ecomm, takes_ctx=True),
    ]
    return FunctionToolset(tools)
