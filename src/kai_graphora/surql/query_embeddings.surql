SELECT
    *,
    vector::similarity::cosine(embedding, $vector) AS dist
FROM type::table($table)
WHERE embedding <|{k}|> $vector;
