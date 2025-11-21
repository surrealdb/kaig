-- -----------------------------------------------------------------------------
-- This tables are created by the vector store configuration. Here we only add
-- the additional fields.
DEFINE FIELD OVERWRITE index ON chunk TYPE int DEFAULT 0;

-- -----------------------------------------------------------------------------
-- Define table: concept
DEFINE TABLE OVERWRITE concept SCHEMALESS;

-- -----------------------------------------------------------------------------
-- Define table: queue
DEFINE TABLE OVERWRITE queue SCHEMALESS;

-- required
DEFINE FIELD OVERWRITE ref ON queue TYPE record<document | chunk>;
DEFINE FIELD OVERWRITE task ON queue TYPE string ASSERT $value IN ["chunk", "infer", "summarize"];

-- optional
DEFINE FIELD OVERWRITE status ON queue TYPE string DEFAULT "pending" ASSERT $value IN ["pending", "processing", "processed", "failed"];
DEFINE FIELD OVERWRITE detail ON queue TYPE option<string> DEFAULT NONE;

-- timestamps
DEFINE FIELD OVERWRITE time ON queue TYPE object DEFAULT {};
DEFINE FIELD OVERWRITE time.created_at ON queue TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD OVERWRITE time.updated_at ON queue TYPE datetime VALUE time::now();
DEFINE FIELD OVERWRITE time.deleted_at ON queue TYPE option<datetime> DEFAULT NONE;

-- -----------------------------------------------------------------------------
-- Define event triggers

DEFINE EVENT OVERWRITE document_create ON document WHEN $event IN ["CREATE", "UPDATE"] THEN {
    $chunk_key = "chunk-" + $after.id.id();
    IF !record::exists(type::thing("queue", $chunk_key)) {
        CREATE type::thing("queue", $chunk_key) CONTENT {
            ref: $after.id,
            task: "chunk"
        }
    }
};

DEFINE EVENT OVERWRITE chunk_create ON chunk WHEN $event IN ["CREATE", "UPDATE"] THEN {
    $infer_key = "infer-" + $after.id.id();
    IF !record::exists(type::thing("queue", $infer_key)) {
        CREATE type::thing("queue", $infer_key) CONTENT {
            ref: $after.id,
            task: "infer"
        };
    };
    $summarize_key = "summarize-" + $after.id.id();
    IF !record::exists(type::thing("queue", $summarize_key)) {
        CREATE type::thing("queue", $summarize_key) CONTENT {
            ref: $after.id,
            task: "summarize"
        }
    }
};
