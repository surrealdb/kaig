-- -----------------------------------------------------------------------------
-- Define table: proc_doc_queue
DEFINE TABLE OVERWRITE proc_doc_queue SCHEMALESS;

DEFINE FIELD OVERWRITE document ON proc_doc_queue TYPE record<document>;
DEFINE FIELD OVERWRITE status ON proc_doc_queue TYPE option<string> DEFAULT NONE;

DEFINE FIELD OVERWRITE time ON proc_doc_queue TYPE object DEFAULT ALWAYS {updated_at: time::now()};
DEFINE FIELD OVERWRITE time.created_at ON proc_doc_queue TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD OVERWRITE time.deleted_at ON proc_doc_queue TYPE option<datetime> DEFAULT NONE;
DEFINE FIELD OVERWRITE time.updated_at ON proc_doc_queue TYPE datetime DEFAULT ALWAYS time::now();

-- -----------------------------------------------------------------------------
-- Define event trigger
DEFINE EVENT OVERWRITE document_create ON document WHEN $event IN ["CREATE", "UPDATE"] THEN {
    IF !record::exists(type::thing("proc_doc_queue", $after.id.id())) {
        CREATE type::thing("proc_doc_queue", $after.id.id()) CONTENT {
            document: $after.id
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
