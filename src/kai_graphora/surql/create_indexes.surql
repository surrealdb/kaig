DEFINE INDEX {index_name}
ON {index_table}
FIELDS embedding
MTREE DIMENSION {dim} DIST COSINE TYPE F32;
