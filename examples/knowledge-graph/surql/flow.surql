-- -----------------------------------------------------------------------------
-- Flows
DEFINE TABLE OVERWRITE flow SCHEMAFULL;

DEFINE FIELD OVERWRITE id ON flow TYPE string;
DEFINE FIELD OVERWRITE table ON flow TYPE string;
DEFINE FIELD OVERWRITE hash ON flow TYPE string;
DEFINE FIELD OVERWRITE dependencies ON flow TYPE array<string>;
DEFINE FIELD OVERWRITE stamp ON flow TYPE string;
DEFINE FIELD OVERWRITE auto_stamp ON flow TYPE bool;
DEFINE FIELD OVERWRITE rerun_when_updated ON flow TYPE bool;
DEFINE FIELD OVERWRITE priority ON flow TYPE int DEFAULT 1;
