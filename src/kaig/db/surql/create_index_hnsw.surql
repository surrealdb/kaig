DEFINE TABLE IF NOT EXISTS {table} SCHEMALESS;
DEFINE FIELD IF NOT EXISTS embedding ON {table} TYPE array<float> | NONE;
DEFINE INDEX IF NOT EXISTS hnsw_idx_{table} ON {table}
    FIELDS embedding
    HNSW DIMENSION {dimension}
    DIST {distance_function}
    TYPE {vector_type}
    EFC 150 M 12 M0 24;
