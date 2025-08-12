-- SELECT *,
--     <-{relation}<-{src} as related
-- FROM $record

SELECT *,
    (IF $embedding {{
        vector::similarity::cosine(embedding, $embedding)
    }} ELSE {{ RETURN None }}) AS similarity
-- OMIT embedding
FROM array::flatten(
    SELECT VALUE
        <-{relation}<-{src}
    FROM $record
)
