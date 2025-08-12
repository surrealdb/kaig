SELECT score, texts, topic, type FROM (
    SELECT
        math::max(score) as score,
        array::group(text) as texts,
        type,
        topic
    FROM (
        SELECT
            type, actions, text, topic,
            (1 - vector::distance::knn()) AS score
        FROM {table}
        WHERE embedding <|{k}{effort_param}|> $embedding
    )
    WHERE score >= $threshold
    GROUP BY topic
)
ORDER BY score DESC
