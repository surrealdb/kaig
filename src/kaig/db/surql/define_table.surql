DEFINE TABLE OVERWRITE {name} SCHEMALESS;

{fields}

DEFINE FIELD OVERWRITE time ON {name} TYPE object DEFAULT {{}};
DEFINE FIELD OVERWRITE time.created_at ON {name} TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD OVERWRITE time.updated_at ON {name} TYPE datetime VALUE time::now();
DEFINE FIELD OVERWRITE time.deleted_at ON {name} TYPE option<datetime> VALUE NONE;
