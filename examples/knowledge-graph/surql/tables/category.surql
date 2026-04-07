DEFINE TABLE OVERWRITE category SCHEMAFULL
    PERMISSIONS
        FOR select FULL,
        FOR create, update, delete NONE;

DEFINE FIELD OVERWRITE name ON TABLE category TYPE string;
DEFINE FIELD OVERWRITE parent ON TABLE category TYPE record<category>;

# embedding field and index are created by kaig
