DEFINE TABLE OVERWRITE product SCHEMAFULL
    PERMISSIONS
        FOR select FULL,
        FOR create, update, delete NONE;

DEFINE FIELD OVERWRITE name ON TABLE product TYPE string;
DEFINE FIELD OVERWRITE description ON TABLE product TYPE string;
DEFINE FIELD OVERWRITE category ON TABLE product TYPE record<category>;

# embedding field and index are created by kaig
