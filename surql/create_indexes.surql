DEFINE INDEX mt_pts
ON appdata_embeddings
FIELDS embedding
MTREE DIMENSION 384 DIST COSINE TYPE F32;

CREATE meta:initialized;
