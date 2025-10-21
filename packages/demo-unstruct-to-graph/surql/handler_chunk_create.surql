DEFINE EVENT OVERWRITE document_create ON document WHEN $event IN ["CREATE", "UPDATE"] THEN {
    http::post("http://0.0.0.0:8080/process", {"doc_id": $after.id.id()});
};

-- DEFINE EVENT OVERWRITE chunk_create ON chunk WHEN $event = "CREATE" THEN {
--     $embedding = http::post($embedding_api_url, $after.content);
--     UPDATE $after.id SET embedding = $embedding;
-- };
