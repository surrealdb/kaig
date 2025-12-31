-- -----------------------------------------------------------------------------
-- This tables are created by the vector store configuration. Here we only add
-- the additional fields.
DEFINE FIELD OVERWRITE index ON chunk TYPE int DEFAULT 0;

-- -----------------------------------------------------------------------------
-- Define table: concept
DEFINE TABLE OVERWRITE concept SCHEMALESS;

-- -----------------------------------------------------------------------------
-- Flows
DEFINE TABLE OVERWRITE flow SCHEMAFULL;

DEFINE FIELD OVERWRITE name ON flow TYPE string;
-- DEFINE FIELD OVERWRITE params ON flow TYPE option<object> DEFAULT NONE;
DEFINE FIELD OVERWRITE table ON flow TYPE string;
DEFINE FIELD OVERWRITE dependencies ON flow TYPE array<string>;
DEFINE FIELD OVERWRITE output ON flow TYPE object;
DEFINE FIELD OVERWRITE output.field ON flow TYPE string;
-- DEFINE FIELD OVERWRITE output.type ON flow TYPE "bool" | "string" | "array<float>";
DEFINE FIELD OVERWRITE priority ON flow TYPE int DEFAULT 1;
