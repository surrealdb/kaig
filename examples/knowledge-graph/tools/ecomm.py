import logfire
from pydantic_ai import RunContext
from tools.deps import Deps

from kaig.db.utils import query

SCHEMA = r"""
-- ------------------------------
-- TABLE: REL_PRODUCT_IN_ORDER
-- ------------------------------

DEFINE TABLE REL_PRODUCT_IN_ORDER TYPE RELATION IN product OUT order SCHEMAFULL PERMISSIONS FOR select FULL, FOR create, update, delete NONE;

DEFINE FIELD in ON REL_PRODUCT_IN_ORDER TYPE record<product> PERMISSIONS FULL;
DEFINE FIELD out ON REL_PRODUCT_IN_ORDER TYPE record<order> PERMISSIONS FULL;
DEFINE FIELD qty ON REL_PRODUCT_IN_ORDER TYPE number PERMISSIONS FULL;

DEFINE INDEX rel_product_in_order_unique_idx ON REL_PRODUCT_IN_ORDER FIELDS in, out UNIQUE;


-- ------------------------------
-- TABLE: category
-- ------------------------------

DEFINE TABLE category TYPE NORMAL SCHEMAFULL PERMISSIONS FOR select FULL, FOR create, update, delete NONE;

DEFINE FIELD embedding ON category TYPE array<float> | none PERMISSIONS FULL;
DEFINE FIELD embedding.* ON category TYPE float PERMISSIONS FULL;
DEFINE FIELD flow_embedded ON category TYPE string | none PERMISSIONS FULL;
DEFINE FIELD name ON category TYPE string PERMISSIONS FULL;
DEFINE FIELD parent ON category TYPE record<category> | none PERMISSIONS FULL;

DEFINE INDEX hnsw_idx_category ON category FIELDS embedding HNSW DIMENSION 1536 DIST COSINE TYPE F32 EFC 150 M 12 M0 24 LM 0.40242960438184466f;


-- ------------------------------
-- TABLE: order
-- ------------------------------

DEFINE TABLE order TYPE NORMAL SCHEMAFULL PERMISSIONS FOR select FULL, FOR create, update, delete NONE;

DEFINE FIELD created_at ON order TYPE datetime READONLY VALUE time::now() PERMISSIONS FULL;
DEFINE FIELD user ON order TYPE record<user> PERMISSIONS FULL;



-- ------------------------------
-- TABLE: product
-- ------------------------------

DEFINE TABLE product TYPE NORMAL SCHEMAFULL PERMISSIONS FOR select FULL, FOR create, update, delete NONE;

DEFINE FIELD category ON product TYPE record<category> PERMISSIONS FULL;
DEFINE FIELD description ON product TYPE string PERMISSIONS FULL;
DEFINE FIELD embedding ON product TYPE array<float> | none PERMISSIONS FULL;
DEFINE FIELD embedding.* ON product TYPE float PERMISSIONS FULL;
DEFINE FIELD flow_embedded ON product TYPE string | none PERMISSIONS FULL;
DEFINE FIELD name ON product TYPE string PERMISSIONS FULL;

DEFINE INDEX hnsw_idx_product ON product FIELDS embedding HNSW DIMENSION 1536 DIST COSINE TYPE F32 EFC 150 M 12 M0 24 LM 0.40242960438184466f;


-- ------------------------------
-- TABLE: review
-- ------------------------------

DEFINE TABLE review TYPE NORMAL SCHEMAFULL PERMISSIONS FOR select FULL, FOR create, update, delete NONE;

DEFINE FIELD embedding ON review TYPE array<float> | none PERMISSIONS FULL;
DEFINE FIELD embedding.* ON review TYPE float PERMISSIONS FULL;
DEFINE FIELD flow_sentiment ON review TYPE string | none PERMISSIONS FULL;
DEFINE FIELD product ON review TYPE record<product> PERMISSIONS FULL;
DEFINE FIELD score ON review TYPE float PERMISSIONS FULL;
DEFINE FIELD sentiment ON review TYPE string | none PERMISSIONS FULL;
DEFINE FIELD text ON review TYPE string PERMISSIONS FULL;
DEFINE FIELD user ON review TYPE record<user> PERMISSIONS FULL;

DEFINE INDEX hnsw_idx_review ON review FIELDS embedding HNSW DIMENSION 1536 DIST COSINE TYPE F32 EFC 150 M 12 M0 24 LM 0.40242960438184466f;


-- ------------------------------
-- TABLE: user
-- ------------------------------

DEFINE TABLE user TYPE NORMAL SCHEMAFULL PERMISSIONS FOR select, update WHERE id = $auth.id, FOR create, delete NONE;

DEFINE FIELD created_at ON user TYPE datetime READONLY VALUE time::now() PERMISSIONS FULL;
DEFINE FIELD deleted_at ON user TYPE none | datetime DEFAULT NONE PERMISSIONS FULL;
DEFINE FIELD display_name ON user TYPE none | string PERMISSIONS FULL;
DEFINE FIELD email ON user TYPE string ASSERT string::is_email($value) PERMISSIONS FULL;
DEFINE FIELD name ON user TYPE string | none PERMISSIONS FULL;
DEFINE FIELD password_hash ON user TYPE string PERMISSIONS FOR select, create, update NONE;
DEFINE FIELD role ON user TYPE string ASSERT $value INSIDE ['user', 'admin'] PERMISSIONS FOR select, create, update NONE;
DEFINE FIELD updated_at ON user TYPE datetime VALUE time::now() PERMISSIONS FULL;
"""


async def query_ecomm(context: RunContext[Deps], question: str) -> str:
    """Queries the database based on a user question.

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
            """-- example query: product sales count by date
SELECT
    in.{id,name} AS product,
    math::sum(qty) AS count
FROM REL_PRODUCT_IN_ORDER
WHERE out IN (
    SELECT VALUE id
    FROM order
    WHERE created_at > d'2026-04-09T12:00:00.0Z'
)
GROUP BY product
ORDER BY count DESC
LIMIT 10;""",
        ]
        # schema = db.query_one("INFO FOR DB")
        surql_query = db.llm.gen_surql(question, SCHEMA, examples)
        results = query(
            db.sync_conn,
            surql_query,
            {},
            dict,
        )

    # TODO: build result string
    result = str(results)

    return result
