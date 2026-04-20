SELECT
    id,
    name,
    description,
    category.{id,name} AS category,
    math::sum(->REL_PRODUCT_IN_ORDER.qty) AS total_sold,
    count(->REL_PRODUCT_IN_ORDER) AS orders_count
OMIT embedding
FROM product;

-- ========================================================
-- Worst (lowest-rated) product reviews across the store — include product, rating, date, and review text
SELECT
    product.{id, name} AS product,
    score AS rating,
    created_at AS date,
    text AS review
FROM review
ORDER BY score ASC, date ASC
LIMIT 10;

-- ========================================================

LET $best = SELECT
    in.{id,name} AS product,
    math::sum(qty) AS total_sold
FROM REL_PRODUCT_IN_ORDER
GROUP BY product
ORDER BY total_sold DESC
LIMIT 3;

RETURN $best.map(|$x|
    $x + {
        reviews: (
            SELECT
                score AS rating,
                created_at AS date,
                text AS review
            FROM review
            WHERE product = $x.product.id
            ORDER BY created_at DESC
        )
    }
);

-- ========================================================

LET $best = SELECT
    in.{id,name} AS product,
    math::sum(qty) AS units_sold
FROM REL_PRODUCT_IN_ORDER
GROUP BY product
ORDER BY units_sold DESC
LIMIT 3;

RETURN $best.map(|$p,$i| $p + {
    rank: $i + 1,
    reviews: (
        SELECT
            id AS review_id,
            score AS rating,
            text AS review_text,
            sentiment,
            flow_sentiment
        FROM review
        WHERE product = $p.product.id
        ORDER BY id DESC
        LIMIT 10
    ),
    avg_score: (SELECT product, math::mean(score) AS avg_score FROM review WHERE product = $p.product.id GROUP BY product)[0].avg_score,
    sentiment_summary: (SELECT product,
        math::sum(IF (score >= 4) {1} ELSE {0}) AS positive,
        math::sum(IF (score >= 2.5 AND score < 4) {1} ELSE {0}) AS neutral,
        math::sum(IF (score < 2.5) {1} ELSE {0}) AS negative
    FROM review WHERE product = $p.product.id GROUP BY product)[0]
});

-- ========================================================
LET $best = SELECT
    in.{id,name} AS product,
    math::sum(qty) AS sold
FROM REL_PRODUCT_IN_ORDER
GROUP BY product
ORDER BY sold DESC
LIMIT 3;

RETURN $best.map(|$x|
    $x + {
        review_stats: (
            SELECT
                product,
                math::mean(score) AS avg_score,
                count() AS review_count,
                math::sum(IF sentiment = 'positive' { 1 } ELSE { 0 }) AS positive_count,
                math::sum(IF sentiment = 'negative' { 1 } ELSE { 0 }) AS negative_count,
                math::sum(IF sentiment = 'neutral' { 1 } ELSE { 0 }) AS neutral_count,
                math::sum(IF flow_sentiment = 'positive' { 1 } ELSE { 0 }) AS flow_sentiment_positive,
                math::sum(IF flow_sentiment = 'negative' { 1 } ELSE { 0 }) AS flow_sentiment_negative
            FROM review
            WHERE product = $x.product.id
            GROUP BY product
        ),
        top_positive_reviews: (
            SELECT id, score, sentiment, flow_sentiment, text
            FROM review
            WHERE product = $x.product.id
            ORDER BY score DESC
            LIMIT 5
        ),
        top_negative_reviews: (
            SELECT id, score, sentiment, flow_sentiment, text
            FROM review
            WHERE product = $x.product.id
            ORDER BY score ASC
            LIMIT 5
        )
    }
);
-- ========================================================



LET $top = SELECT
    in.{id,name} AS product,
    math::sum(qty) AS total_sales
FROM REL_PRODUCT_IN_ORDER
GROUP BY product
ORDER BY total_sales DESC
LIMIT 3;

RETURN $top.map(|$p|
    $p + {
        average_rating: (
            SELECT product, math::mean(score) AS avg_rating, math::sum(1) AS review_count
            FROM review
            WHERE product = $p.product.id
            GROUP BY product
        )[0].avg_rating,
        review_count: (
            SELECT product, math::mean(score) AS avg_rating, math::sum(1) AS review_count
            FROM review
            WHERE product = $p.product.id
            GROUP BY product
        )[0].review_count,
        sentiment_breakdown: (
            SELECT sentiment, math::sum(1) AS count
            FROM review
            WHERE product = $p.product.id
            GROUP BY sentiment
            ORDER BY count DESC
        ),
        recent_reviews: (
            SELECT score AS rating, created_at AS date, text, sentiment, flow_sentiment
            FROM review
            WHERE product = $p.product.id
            ORDER BY created_at DESC
            LIMIT 10
        )
    }
);

-- =================================================

SELECT
    id AS customer_id,
    name,
    email,
    -- total lifetime spend (uses product.price if present; missing price treated as 0)
    (
        SELECT math::sum(
            IF in.price { in.price * qty } ELSE { 0 }
        )
        FROM REL_PRODUCT_IN_ORDER
        WHERE out IN (SELECT VALUE id FROM order WHERE user = user.id)
        GROUP ALL
    ) AS total_spend,
    -- number of orders
    count(SELECT id FROM order WHERE user = $parent.id) AS order_count,
    -- date of most recent order
    (SELECT VALUE time::max(created_at) FROM ONLY order WHERE user = user.id GROUP ALL) AS last_order_date,
    -- top 5 products by quantity purchased for this customer
    (
        SELECT in.{id,name} AS product, math::sum(qty) AS qty
        FROM REL_PRODUCT_IN_ORDER
        WHERE out.user = $parent.id
        GROUP BY product
        ORDER BY qty DESC
        LIMIT 5
    ) AS top_products
FROM user
ORDER BY total_spend DESC
LIMIT 1;

-- ==================================================================

LET $top_customer = SELECT
    id,
    name,
    email,
    (SELECT VALUE count(id) FROM ONLY order WHERE user = $parent.id GROUP ALL) AS order_count,
    (SELECT VALUE created_at FROM ONLY order WHERE user = $parent.id ORDER BY created_at DESC LIMIT 1) AS last_order_date,
    (SELECT VALUE math::sum(qty * in.price) FROM ONLY REL_PRODUCT_IN_ORDER WHERE out.user = $parent.id GROUP ALL) AS total_spend
FROM user
ORDER BY total_spend DESC
LIMIT 1;

RETURN $top_customer.map(|$u|
    $u + {
        top_products: (
            SELECT
                in.{id,name} AS product,
                math::sum(qty) AS total_qty,
                math::sum(qty * in.price) AS total_spend
            FROM REL_PRODUCT_IN_ORDER
            WHERE out.user = $u.id
            GROUP BY product
            ORDER BY total_qty DESC
            LIMIT 5
        )
    }
);

-- =================================================================

LET $best = SELECT
    out.user AS customer,
    math::sum(qty * IF in.price { in.price } ELSE { 0 }) AS total_spend,
    time::max(out.created_at) AS last_order_date
FROM REL_PRODUCT_IN_ORDER
GROUP BY customer
ORDER BY total_spend DESC
LIMIT 1;

LET $cust_orders = SELECT VALUE id FROM order WHERE user = $best[0].customer.id;

LET $order_count = count($cust_orders);

LET $top_products = SELECT
    in.{id,name} AS product,
    math::sum(qty) AS qty
FROM REL_PRODUCT_IN_ORDER
WHERE out IN $cust_orders
GROUP BY product
ORDER BY qty DESC
LIMIT 5;

RETURN {
    customer_id: $best[0].customer.id,
    email: $best[0].customer.email,
    total_spend: $best[0].total_spend,
    order_count: $order_count,
    last_order_date: $best[0].last_order_date,
    top_products: $top_products.map(|$p| $p.product)
};

-- ===================================================================

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

-- ===================================================================

LET $worst = SELECT
    product.{id,name} AS product,
    math::mean(score) AS avg_rating
FROM review
GROUP BY product
ORDER BY avg_rating ASC
LIMIT 1;

RETURN $worst.map(|$x| $x + {
    review_count: (SELECT VALUE count() FROM review WHERE product = $x.product.id GROUP ALL),
    common_complaints: (
        SELECT text, score
        FROM review
        WHERE product = $x.product.id
        ORDER BY score ASC
        LIMIT 5
    )
});

-- =======================================================================

LET $productRecord = product:10;
LET $total = SELECT VALUE math::sum(qty)
FROM ONLY REL_PRODUCT_IN_ORDER
WHERE in.id = $productRecord
GROUP ALL;
RETURN $total;

LET $distinct_orders = SELECT VALUE count()
FROM ONLY order
WHERE id IN (SELECT VALUE out FROM REL_PRODUCT_IN_ORDER WHERE in = $productRecord)
GROUP ALL;

RETURN {
    product_id: $productRecord,
    total_units_sold: $total,
    distinct_orders_count: $distinct_orders
};

-- =====================================================================

-- DON'T use $parent when it's refering a GROUP
SELECT
    in.{id,name,price} AS product,
    math::sum(in.price * qty) AS total_revenue,
    math::sum(qty) AS total_units,
    (SELECT VALUE count()
        FROM ONLY REL_PRODUCT_IN_ORDER
        WHERE in = $parent.product.id
        GROUP ALL
    ) AS distinct_orders
FROM REL_PRODUCT_IN_ORDER
GROUP BY product
ORDER BY total_revenue DESC
LIMIT 1;

-- DO: extend results to avoid $parent references in subqueries of GROUP selects
LET $x = SELECT
        in.{id,name,price} AS product,
        math::sum(in.price * qty) AS total_revenue,
        math::sum(qty) AS total_units
    FROM ONLY REL_PRODUCT_IN_ORDER
    GROUP BY product
    ORDER BY total_revenue DESC
    LIMIT 1;

-- extend with count of distinct_orders
RETURN $x + {
    distinct_orders: count(
        SELECT id
        FROM REL_PRODUCT_IN_ORDER
        WHERE in = $x.product.id
    )
};


-- =======================================================================

SELECT
    in.{id,name} AS product,
    math::sum(in.price * qty) AS total_revenue,
    math::sum(qty) AS total_units_sold,
    count() AS distinct_orders
FROM REL_PRODUCT_IN_ORDER
GROUP BY product
ORDER BY total_revenue DESC
LIMIT 1;

-- =======================================================================

SELECT
    out.user.{id, name, email} AS customer,
    math::sum(qty) AS total_units,
    math::sum(in.price * qty) AS total_spent,
    time::max(out.created_at) AS last_purchase_date
FROM REL_PRODUCT_IN_ORDER
WHERE in.id() = 26
GROUP BY customer
ORDER BY last_purchase_date DESC;

-- =======================================================================

SELECT
  out.user.{id,name,email} AS customer,
  math::sum(qty) AS total_units,
  math::sum(in.price * qty) AS total_spent,
  time::max(out.created_at) AS last_purchase_date
FROM REL_PRODUCT_IN_ORDER
WHERE in = product:26
GROUP BY customer
ORDER BY last_purchase_date DESC;
