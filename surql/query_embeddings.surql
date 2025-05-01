SELECT
    appid,
    text,
    vector::similarity::cosine(embedding, $vector) AS dist
FROM appdata_embeddings
WHERE embedding <|5|> $vector;
