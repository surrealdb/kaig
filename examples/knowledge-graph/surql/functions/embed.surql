DEFINE FUNCTION OVERWRITE fn::embed($text: string) {
    RETURN http::post('https://api.openai.com/v1/embeddings', {
        input: $text,
        model: 'text-embedding-3-small',
        encoding_format: 'float'
    }, {
        'Authorization': 'Bearer ' + $OPENAI_API_KEY,
        'Content-Type': 'application/json'
    }).data[0].embedding;
};
