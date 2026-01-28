{
LET $sub_query = SELECT VALUE
    chunks.map(|$chunk| {
        index: $chunk.index,
        concept: id,
        chunk: $chunk.id,
        content: $chunk.content,
        doc: $chunk.doc,
        score: score
    }) AS x
    FROM (
        SELECT *,
            <-MENTIONS_CONCEPT<-chunk.{id, doc, index, content} AS chunks
        FROM (
            SELECT *,
                (1 - vector::distance::knn()) AS score
            OMIT embedding
            FROM concept
            WHERE embedding <|5,40|> $embedding
        )
        WHERE score >= $threshold
    );

RETURN SELECT
    doc.{id, filename, content_type} as doc,
    array::group({
        id: chunk,
        chunk_index: index,
        score: max_score,
        content: content
    }) AS chunks,
    math::max(max_score) AS best_score
FROM (
    SELECT
        doc,
        chunk,
        index,
        content,
        math::max(score) AS max_score,
        array::group(concept) AS concepts
    FROM array::flatten($sub_query)
    GROUP BY chunk
)
GROUP BY doc
ORDER BY best_score DESC;
}
