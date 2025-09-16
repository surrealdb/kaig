-- Prepare the table
{
    REMOVE TABLE IF EXISTS documents;
    DEFINE TABLE documents;
    DEFINE FIELD text ON documents TYPE string;
    DEFINE FIELD embedding ON documents TYPE array<float, 4>;
};

-- Vector index
-- Reference: https://surrealdb.com/docs/surrealdb/reference-guide/vector-search
DEFINE INDEX IF NOT EXISTS documents_vec_index
    ON TABLE documents
    FIELDS embedding
    MTREE DIMENSION 4 DIST COSINE TYPE F32
    CONCURRENTLY;

-- Add some documents with their embeddings
{
    CREATE documents CONTENT { text: "foo", embedding: [1f, 2f, 3f, 4f] };
    CREATE documents CONTENT { text: "bar", embedding: [2f, 2f, 2f, 2f] };
    CREATE documents CONTENT { text: "zar", embedding: [5f, 4f, 3f, 2f] };
};

-- Search query
LET $vector = [1f, 1f, 1f, 1f];

SELECT
    *,
    // knn() uses the distance function from the index
    (1 - vector::distance::knn()) AS score
    // while the following gets computed independently from the index
    // vector::similarity::cosine(embedding, $vector) AS similarity
    OMIT embedding // ignore the embedding in the result
    FROM documents
    WHERE embedding <|2|> $vector;

-- This shows the index, in the `indexes` attribute
-- INFO FOR TABLE documents;
