-- example query: total product items sold
SELECT *,
    math::sum(->REL_PRODUCT_IN_ORDER.qty) AS total
OMIT embedding
FROM product;

-- example query: top product sales after date
SELECT
    in.{id,name} AS product,
    math::sum(qty) AS count
FROM REL_PRODUCT_IN_ORDER
WHERE out IN (
    SELECT VALUE id FROM order WHERE created_at > d'2026-04-09T12:00:00.0Z'
)
GROUP BY product
ORDER BY count DESC
LIMIT 10;

-- example query: top product sales extended with their reviews
LET $since = d'2026-03-07T12:00:00.0Z';
LET $best = (
    SELECT
        in.{id,name} AS product,
        math::sum(qty) AS count
    FROM REL_PRODUCT_IN_ORDER
    WHERE out IN (
        SELECT VALUE id FROM order WHERE created_at > $since
    )
    GROUP BY product
    ORDER BY count DESC
    LIMIT 10
);

-- extend each product with its reviews since $since ordered by descending score
RETURN $best.map(|$x| $x + {
    reviews: (
        SELECT * FROM review
        WHERE product = $x.product.id AND created_at > $since
        ORDER BY score DESC
    )
});

--- example query: top 5 customers
SELECT
    id AS customer_id,
    email,
    (
        SELECT VALUE math::sum(in.price * qty)
        FROM ONLY REL_PRODUCT_IN_ORDER
        WHERE out.user = $parent.id
        GROUP ALL
    ) AS total_spend,
    (SELECT VALUE math::sum(1) FROM ONLY order WHERE user = $parent.id GROUP ALL) AS order_count,
    (SELECT VALUE created_at FROM ONLY order WHERE user = $parent.id ORDER BY created_at DESC LIMIT 1) AS last_order_date
FROM user
ORDER BY total_spend DESC
LIMIT 5;

--- Example: avoid using VALUE and ORDER BY together

-- WRONG
-- Parse error: Missing order idiom `out.created_at` in statement selection
SELECT VALUE out.id
FROM ONLY REL_PRODUCT_IN_ORDER
ORDER BY out.created_at DESC
LIMIT 1;

-- CORRECT
-- Order-by field included in selected fields.
(
    SELECT
        out.id AS id,
        out.created_at
    FROM ONLY REL_PRODUCT_IN_ORDER
    ORDER BY out.created_at DESC
    LIMIT 1
).id;
