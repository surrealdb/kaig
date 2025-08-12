SELECT *, score
FROM (
    SELECT *, (1 - vector::distance::knn()) AS score
    FROM {table}
    WHERE embedding <|{k}{effort_param}|> $embedding
)
WHERE score >= $threshold
ORDER BY score DESC
