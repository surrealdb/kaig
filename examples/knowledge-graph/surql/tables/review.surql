DEFINE TABLE OVERWRITE review SCHEMAFULL
    PERMISSIONS
        FOR select FULL,
        FOR create, update, delete NONE;

DEFINE FIELD OVERWRITE text ON TABLE review TYPE string;
DEFINE FIELD OVERWRITE score ON TABLE review TYPE float;
DEFINE FIELD OVERWRITE sentiment ON TABLE review TYPE string | NONE;
DEFINE FIELD OVERWRITE user ON TABLE review TYPE record<user>;

# embedding field and index are created by kaig
