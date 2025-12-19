LET $sub_query = SELECT VALUE
    chunks.map(|$chunk| {
        index: $chunk.index,
        concept: id,
        chunk: $chunk.id,
        doc: $chunk.doc,
        score: score
    }) AS x
    FROM (
        SELECT *,
            <-MENTIONS_CONCEPT<-chunk.{id, doc, index} AS chunks
        FROM (
            SELECT *,
                (1 - vector::distance::knn()) AS score
            OMIT embedding
            FROM concept
            WHERE embedding <|5,40|> $embedding
        )
        WHERE score >= $threshold
    );

SELECT
    doc,
    array::group({
        chunk: chunk,
        index: index,
        max_score: max_score,
        concepts: concepts
    }) AS chunks,
    math::max(max_score) AS best_concept_score
FROM (
    SELECT
        doc,
        chunk,
        index,
        math::max(score) AS max_score,
        array::group(concept) AS concepts
    FROM array::flatten($sub_query)
    GROUP BY chunk
)
GROUP BY doc
ORDER BY best_concept_score DESC;
