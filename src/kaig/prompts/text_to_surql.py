PROMPT_GEN_SURQL = """
You are an expert in SurrealQL (surql, SurrealDB's query language).

Generate a valid surql query to get the information required to answer the user's prompt.

PROMPT: {prompt}

SCHEMA:
```
{schema}
```

NOTES:
- use `GROUP BY` or `GROUP ALL` when aggregating fields with math::mean, math::sum, etc.
- `SELECT product, math::mean(score) AS avg_score FROM review WHERE product = $p.product.id GROUP BY product`.
- don't use $parent in a subquery of a SELECT with GROUP. Instead, run the subquery separately and assign it to a variable, and then run the main query with the variable.
- if you `ORDER BY` a field, make sure to include the field in the SELECT fields.
- Count example: `count(SELECT id FROM order WHERE user = $parent.id) AS order_count`
- ALWAYS `OMIT` the `embedding` field from the result to avoid large result sets.
{notes}

DON'T:
- don't use `math::avg`, the correct one is `math::mean`.
- don't use `?` and `:` to build JS-like inline conditionals, use `IF $x {{ $foo }} ELSE {{ $bar }}`.
- don't count records using `count(*)`. Use: `count()`, and make sure to include `GROUP BY` or `GROUP ALL` when aggregating.
- don't use `math::max(created_at)` when the field is a timestamp, use `time::max(created_at)` instead.
- don't use unnecessary subqueries like `WHERE out IN (SELECT VALUE id FROM order WHERE user = $parent.id)`. Instead, do this `WHERE out.user = $parent.id`.
- don't filter by id like this `id = 26`. You should do `id = table_name:26` or `id.id() = 26`.
- don't use `~` nor `LIKE` to filter by text similarity. Use `string::similarity::jaro(string, string)` (which returns a similarity score between 0 and 1) or `fn::embed` to generate embeddings and `vector::similarity::cosine(array, array)` to compare them.
- don't use `string::lower`, use `string::lowercase` instead.
- don't create arrays with parethesis when using `IN`, use `[]` instead. For example `WHERE id IN [review:r01, review:r02]`
- don't alias tables in the `FROM` clause, use the table name directly. E.g: `FROM review AS r` DOES NOT WORK in SurQL.
- don't `SELECT product = product.{{id, name}}`. Instead DO `SELECT product.{{id,name}} AS product`.

DO:
- when using `OMIT`, it should go before the `FROM` statement, after the SELECT fields.
- `UPDATE` should return only the required fields to avoid large result sets. E.g: `UPDATE product:1 SET price = 10.0 RETURN id, name, price;`.

EXAMPLES:
```
{examples}
```

PROMPT: {prompt}
"""
