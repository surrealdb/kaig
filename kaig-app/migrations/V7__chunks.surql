DEFINE TABLE OVERWRITE chunk SCHEMAFULL
    PERMISSIONS
        FOR select WHERE $auth.id = $this.doc.owner,
        FOR create, update, delete NONE;

DEFINE FIELD OVERWRITE content ON TABLE chunk TYPE string;

# embedding field and index is created by the python ingestion script

-- DEFINE TABLE OVERWRITE REL_CHUNK_HAS_KEYWORD SCHEMAFULL
--     TYPE RELATION IN chunk OUT keyword
--     PERMISSIONS
--         FOR select FULL,
--         FOR create, update, delete NONE;

-- DEFINE INDEX IF NOT EXISTS rel_chunk_has_keyword_unique_idx ON REL_CHUNK_HAS_KEYWORD FIELDS in, out UNIQUE;
