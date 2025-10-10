--  .d8888b.                                             888 8888888b.  888888b.
-- d88P  Y88b                                            888 888  'Y88b 888  '88b
-- Y88b.                                                 888 888    888 888  .88P
--  'Y888b.   888  888 888d888 888d888  .d88b.   8888b.  888 888    888 8888888K.
--     'Y88b. 888  888 888P'   888P'   d8P  Y8b     '88b 888 888    888 888  'Y88b
--       '888 888  888 888     888     88888888 .d888888 888 888    888 888    888
-- Y88b  d88P Y88b 888 888     888     Y8b.     888  888 888 888  .d88P 888   d88P
--  'Y8888P'   'Y88888 888     888      'Y8888  'Y888888 888 8888888P'  8888888P'
--
--
-- Welcome to SurrealDB — the database that adapts to your data, not the other
-- way around. SurrealDB is a multi-model database combining Graph, Document,
-- Relational, Time-Series, and Vector capabilities in one system, all powered
-- by SurrealQL. Use it to build AI agents, as a backend, a BaaS, or embed it
-- directly into your apps — one engine, every model.
--
-- Learn more at https://surrealdb.com/docs/surrealdb/introduction/start
--
-- *****************************************************************************


// ## Setup:
//
// - Download Ollama, and pull the models you are going to use
// - Run the AI service with:
//   ```
//   cargo run -- --embeddings-model all-minilm:22m --llm-model llama3.2:latest
//   ```


-- =============================================================================
-- Vector index for embeddings

DEFINE INDEX IF NOT EXISTS documents_vec_index ON TABLE documents
    FIELDS embedding MTREE DIMENSION 384 DIST COSINE TYPE F32;

-- =============================================================================
-- API endpoints for generating embeddings and answers

DEFINE PARAM OVERWRITE $embedding_api_url VALUE "http://localhost:8080/embed";
DEFINE PARAM OVERWRITE $llm_generate_api_url VALUE "http://localhost:8080/generate";
-- DEFINE PARAM OVERWRITE $llm_generate_api_url VALUE "https://rag-demo.requestcatcher.com/";

-- =============================================================================
-- Custom function to execute a similarity search using the vector index

DEFINE FUNCTION OVERWRITE fn::search($txt: string, $threshold: float) {
    $embedding = http::post($embedding_api_url, $txt);
    RETURN SELECT text, score FROM (
        SELECT
            text,
            (1 - vector::distance::knn()) AS score
        FROM documents
        WHERE embedding <|10|> $embedding
    ) WHERE score >= $threshold;
};

-- =============================================================================
-- Insert documents in vector store

$texts = [
    -- "RAG stands for Retrieve, Augment, and Generate; it is an AI technique to provide LLMs with context to provibe better answers.",
    -- "AI agents are autonomous processes that are created to take a task and provide an answer, or trigger a tool. They usually are provided with 1) an LLM for reassoning, summarizing, and generating answers in NL, 2) a system prompt to guide the LLM into accomplishing the task it's designed to do, and 3) tools it can decide to use as part of it's process, like integrations with search engines, MCP servers, file system, or external APIs",
    -- "SurrealDB is a multi-modal DB that can store, index, and query AI knowledge and memory, using vector embeddings, relational data, graph links, and built-in and custom functions",
    -- "AI frameworks help developers create agents by providing an interface for the knowledge and memory stored in SurrealDB",
    -- "To build a knowledge base from files, you need to turn those files (unstructured data) into chunks (plain text) and identify concepts and their relationships (nodes and edges). The text can be stored in a vector store, and the nodes and enges are used to build the graph"
    "spaceship thrusters require maintenance every 258 hours, unless they have hybrid systems and kers, in that case they require an additional electrical maintance every 60 natural days [maintenance,spaceship]",
    "spaceship seats require thorough integrity checks every year [maintenance,spaceship]",
    "you are in the main base station in planet A-32z. We maintain planet earth's clock, and the main language is creole spanglish [planet]",
    "satellite communication is free of charge, but availability is not guaranteed. Requirements: valid biometric membership [membership]",
    "uniforms have to be requested 2 weeks in advance. You need to provide your body meassures (arm, seam, chest) and pick 3 colors [membership]",
    "helmets are not required, the spaceships provide all safety needed [safety]",
    "population size is unknown, but estimated around 100,000 and 3,000,000 [planet]"
];

for $i in 0..$texts.len() {
    $embedding = http::post($embedding_api_url, $texts[$i]);
    UPSERT type::thing("documents", $i) CONTENT { text: $texts[$i], embedding: $embedding };
};

-- =============================================================================
-- System prompt for the LLM to use when generating answers
-- LET $sys_prompt = "You are an AI engineer expert, and your goal is to provide very short 1-sentence answers to the users questions, based on the provided \"Context\". Users are trying to figure out how to build AI solutions, and you need to guide them step by step, starting with the basics. Give your 1-sentence answer, and suggest the user what to ask about next.\n\n## Question:\n{prompt}\n\n## Context:\n{context}";
LET $sys_prompt = "You are a super efficient AI assitant for residents of planet A-32z. Your task is to answer people's questions based on the provided \"Context\". Rephrase the user's question to acknowledge you understood, and give a very short answer. Offer additional help. Use emojis instead of words as much as possible to reduce characters.\n\n## Question:\n{prompt}\n\n## Context:\n{context}";

-- =============================================================================
-- Execute a similarity search for the user's question

-- LET $question = "how can i create a knowledge graph from documents for my AI agent?";
LET $question = "how often should i check my spaceship?";
RETURN "Similarity search: '" + $question + "'. Results ⤵️";

-- similarity search
LET $results = fn::search($question, 0.5);
RETURN $results;

-- LLM answer
LET $payload = {
    "sys_prompt": $sys_prompt,
    "usr_prompt": $question,
    "context": $results.map(|$res| $res.text).join("\n\n")
};
RETURN "LLM generated answer ⤵️";
RETURN http::post($llm_generate_api_url, $payload);

-- Try another one
--
-- LET $question = "what is RAG?";
-- http::post($llm_generate_api_url, {"sys_prompt": $sys_prompt, "usr_prompt": fn::search($question, 0.65)[0].text});

-- =============================================================================
-- Read more:
-- ----------
--
-- - Build an Agent using SurrealDB and Agno: https://surrealdb.com/blog/TODO
-- - Vector index reference: https://surrealdb.com/docs/surrealdb/reference-guide/vector-search
--
-- Need help, contact us: TODO
