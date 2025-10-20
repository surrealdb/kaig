DEFINE EVENT OVERWRITE chunk_create ON chunk WHEN $event = "CREATE" THEN {
    $embedding = http::post($embedding_api_url, $after.content);
    UPDATE $after.id SET embedding = $embedding;
};
