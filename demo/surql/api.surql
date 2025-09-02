DEFINE PARAM OVERWRITE $embedding_api_url VALUE "http://host.docker.internal:8080/embed";

-- Search function
--
DEFINE FUNCTION OVERWRITE fn::search($table: string, $txt: string, $threshold: float) {
    $embedding = http::post($embedding_api_url, $txt);
    RETURN SELECT id, content, score FROM (
        SELECT
            id, content,
            math::max(score) as score
        FROM (
            SELECT
                id, content,
                (1 - vector::distance::knn()) AS score
            FROM type::table($table)
            WHERE embedding <|50,17|> $embedding
        )
        WHERE score >= $threshold
    )
    ORDER BY score DESC;
};
-- Example call:
-- RETURN fn::search("documents", "hello world", 0.5);

-- Search API
--
-- TODO: why doesn't it work if I remove `get`?
DEFINE API OVERWRITE "/search-text"
    FOR get, post
        MIDDLEWARE
            api::req::raw_body(false)
        THEN {
            RETURN {
                status: 200,
                body: {
                    response: fn::search($request.body.table, $request.body.text, $request.body.threshold)
                },
                headers: {
                    'last-modified': time::now(),
                    'expires': time::now() + 4d
                }
            };
        };
-- Example call:
-- api::invoke("/search-text", {
--     body: {table:"documents", text:"hello world", threshold:0.5}
-- });
