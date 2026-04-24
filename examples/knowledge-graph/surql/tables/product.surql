DEFINE TABLE OVERWRITE product SCHEMAFULL
    PERMISSIONS
        FOR select FULL,
        FOR create, update, delete NONE;

DEFINE FIELD OVERWRITE name ON TABLE product TYPE string;
DEFINE FIELD OVERWRITE description ON TABLE product TYPE string;
DEFINE FIELD OVERWRITE category ON TABLE product TYPE record<category>;
DEFINE FIELD OVERWRITE price ON TABLE product TYPE float DEFAULT rand::float(1, 100);

DEFINE FIELD OVERWRITE flow_embedded ON TABLE product TYPE string | NONE;

# embedding field and index are created by kaig
