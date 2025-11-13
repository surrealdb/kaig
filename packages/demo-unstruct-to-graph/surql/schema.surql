-- -----------------------------------------------------------------------------
-- Define table: queue
DEFINE TABLE OVERWRITE queue SCHEMALESS;

-- required
DEFINE FIELD OVERWRITE ref ON queue TYPE record<document | chunk>;
DEFINE FIELD OVERWRITE task ON queue TYPE string ASSERT $value IN ["chunk", "infer"];

-- optional
DEFINE FIELD OVERWRITE status ON queue TYPE string DEFAULT "pending" ASSERT $value IN ["pending", "processed", "failed"];
DEFINE FIELD OVERWRITE detail ON queue TYPE option<string> DEFAULT NONE;

-- timestamps
DEFINE FIELD OVERWRITE time ON queue TYPE object DEFAULT ALWAYS { updated_at: time::now() };
DEFINE FIELD OVERWRITE time.created_at ON queue TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD OVERWRITE time.deleted_at ON queue TYPE option<datetime> DEFAULT NONE;
DEFINE FIELD OVERWRITE time.updated_at ON queue TYPE datetime DEFAULT ALWAYS time::now();

-- -----------------------------------------------------------------------------
-- Define event triggers

DEFINE EVENT OVERWRITE document_create ON document WHEN $event IN ["CREATE", "UPDATE"] THEN {
    IF !record::exists(type::thing("queue", $after.id.id())) {
        CREATE type::thing("queue", $after.id.id()) CONTENT {
            ref: $after.id,
            task: "chunk"
        }
    }
};

DEFINE EVENT OVERWRITE chunk_create ON chunk WHEN $event IN ["CREATE", "UPDATE"] THEN {
    IF !record::exists(type::thing("queue", $after.id.id())) {
        CREATE type::thing("queue", $after.id.id()) CONTENT {
            ref: $after.id,
            task: "infer"
        }
    }
};

-- DEFINE EVENT OVERWRITE document_create ON document WHEN $event IN ["CREATE", "UPDATE"] THEN {
--     http::post("http://0.0.0.0:8080/process", {"doc_id": $after.id.id()});
-- };

-- DEFINE EVENT OVERWRITE chunk_create ON chunk WHEN $event = "CREATE" THEN {
--     $embedding = http::post($embedding_api_url, $after.content);
--     UPDATE $after.id SET embedding = $embedding;
-- };
