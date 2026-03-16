DEFINE TABLE IF NOT EXISTS {name} SCHEMALESS;

{fields}

DEFINE FIELD IF NOT EXISTS created_at ON {name} TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD IF NOT EXISTS updated_at ON {name} TYPE datetime VALUE time::now();
DEFINE FIELD IF NOT EXISTS deleted_at ON {name} TYPE option<datetime> VALUE NONE;
