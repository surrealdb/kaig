SELECT
    best_chunk_score,
    summary,
    doc.{id, filename, content_type},
    array::transpose([
        contents,
        scores,
        chunks,
        chunk_indexes
    ]).map(|$arr| {
        content: $arr[0],
        score: $arr[1],
        id: $arr[2],
        chunk_index: $arr[3]
    }) AS chunks
FROM (
    SELECT
        doc,
        summary,
        math::max(score) AS best_chunk_score,
        array::group(content) AS contents,
        array::group(score) AS scores,
        array::group(id) AS chunks,
        array::group(index) AS chunk_indexes
        FROM (
            SELECT *,
                (1 - vector::distance::knn()) AS score
                OMIT embedding
            FROM chunk
            WHERE embedding <|5,40|> $embedding
            ORDER BY index ASC
        )
        WHERE score >= $threshold
        GROUP BY doc
        ORDER BY best_chunk_score DESC
);
