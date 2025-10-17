DEFINE TABLE OVERWRITE {table} SCHEMALESS;
DEFINE FIELD OVERWRITE embedding ON {table} TYPE array<float>;
DEFINE INDEX OVERWRITE mtree_idx_{table} ON {table}
    FIELDS embedding
    MTREE DIMENSION {dimension}
    DIST {distance_function}
    TYPE {vector_type}
    CAPACITY 40 DOC_IDS_ORDER 100 DOC_IDS_CACHE 100 MTREE_CACHE 100;
