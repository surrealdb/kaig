DEFINE PARAM OVERWRITE $embedding_api_url VALUE "http://127.0.0.1:8080/embed";
DEFINE PARAM OVERWRITE $docs_table VALUE "document";

DEFINE FUNCTION OVERWRITE fn::search($txt: string, $threshold: float) {
    $embedding = http::post($embedding_api_url, $txt);
    RETURN SELECT id, content, score FROM (
        SELECT
            id, content,
            math::max(score) as score
        FROM (
            SELECT
                id, content,
                (1 - vector::distance::knn()) AS score
            FROM type::table($docs_table)
            WHERE embedding <|50,17|> $embedding
        )
        WHERE score >= $threshold
    )
    ORDER BY score DESC;
};

-- RETURN fn::search("hello world", 0.5);

-- TODO: why doesn't it work if I remove `get`?
DEFINE API OVERWRITE "/search-text" FOR get, post
    MIDDLEWARE
        api::req::raw_body(false)
    THEN {
        RETURN {
            status: 200,
            body: {
                response: fn::search($request.body.text, $request.body.threshold)
            },
            headers: {
                'last-modified': time::now(),
                'expires': time::now() + 4d
            }
        };
    };

-- Invoke:
-- api::invoke("/search-text", {
--     body: {text:"hello world", threshold:0.5}
-- });
