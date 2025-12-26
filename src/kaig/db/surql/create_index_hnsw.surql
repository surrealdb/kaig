DEFINE TABLE OVERWRITE {table} SCHEMALESS;
DEFINE FIELD OVERWRITE embedding ON {table} TYPE array<float>;
DEFINE INDEX OVERWRITE hnsw_idx_{table} ON {table}
    FIELDS embedding
    HNSW DIMENSION {dimension}
    DIST {distance_function}
    TYPE {vector_type}
    EFC 150 M 12 M0 24;
