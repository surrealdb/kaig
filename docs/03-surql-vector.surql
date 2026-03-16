-- Prepare the table
{
    DEFINE TABLE documents;
    DEFINE FIELD text ON documents TYPE string;
    DEFINE FIELD embedding ON documents TYPE array<float, 4>;
};

-- Vector index
-- Reference: https://surrealdb.com/docs/surrealdb/models/vector
DEFINE INDEX OVERWRITE documents_vec_index
    ON TABLE documents
    FIELDS embedding
    HNSW DIMENSION 4 DIST COSINE TYPE F32;

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
    WHERE embedding <|2,40|> $vector;

-- This shows the index, in the 'indexes' attribute
-- INFO FOR TABLE documents;


-- ------------------------------------------------------------
-- Functions
// The above search query can be turned into a function for ease of use


DEFINE FUNCTION OVERWRITE fn::search($vector: array<float>) {
    RETURN SELECT
        *,
        (1 - vector::distance::knn()) AS score
    OMIT embedding
    FROM documents
    WHERE embedding <|2,40|> $vector;
};

RETURN fn::search([1f, 2f, 3f, 4f]);

-- Congratulations, you've finished the onboarding!
-- Get your certificate by completing the SurrealDB University Fundamentals
-- See more examples in:
-- https://surrealdb.com/docs/labs?filters=demos%2Cexamples%2Csurrealdb+official
