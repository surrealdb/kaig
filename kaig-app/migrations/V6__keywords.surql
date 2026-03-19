DEFINE TABLE OVERWRITE keyword SCHEMAFULL
    PERMISSIONS
        FOR select FULL,
        FOR create, update, delete NONE;

DEFINE FIELD OVERWRITE content ON TABLE keyword TYPE string;

# embedding field and index is created by the python ingestion script

DEFINE TABLE OVERWRITE REL_FILE_HAS_KEYWORD SCHEMAFULL
    TYPE RELATION IN file OUT keyword
    PERMISSIONS
        FOR select FULL,
        FOR create, update, delete NONE;

DEFINE INDEX IF NOT EXISTS rel_file_has_keyword_unique_idx ON REL_FILE_HAS_KEYWORD FIELDS in, out UNIQUE;
