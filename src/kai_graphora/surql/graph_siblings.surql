SELECT VALUE
    (
        SELECT *,
            vector::similarity::cosine(embedding, $parent.embedding) AS similarity
        -- OMIT embedding
        FROM array::distinct(->{relation}->{dest}<-{relation}<-{src} || [])
    ) AS siblings
FROM ONLY $record
FETCH siblings
