DEFINE TABLE OVERWRITE order SCHEMAFULL
    PERMISSIONS
        FOR select FULL,
        FOR create, update, delete NONE;

DEFINE FIELD OVERWRITE user ON TABLE order TYPE record<user>;

DEFINE FIELD OVERWRITE created_at ON TABLE order TYPE datetime VALUE time::now() READONLY;

# embedding field and index are created by kaig
