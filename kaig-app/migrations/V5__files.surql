DEFINE TABLE OVERWRITE file SCHEMAFULL
    PERMISSIONS
        FOR select WHERE owner = $auth.id OR $auth.role = "admin",
        FOR create WHERE owner = $auth.id,
        FOR update WHERE owner = $auth.id,
        FOR delete WHERE owner = $auth.id;

DEFINE FIELD OVERWRITE owner ON TABLE file TYPE record<user>;
DEFINE FIELD OVERWRITE filename ON TABLE file TYPE string;
DEFINE FIELD OVERWRITE parent ON file TYPE option<record<file>> DEFAULT NONE;
DEFINE FIELD OVERWRITE content_type ON TABLE file TYPE string;
DEFINE FIELD OVERWRITE chunking_metadata ON TABLE file TYPE option<object> FLEXIBLE DEFAULT NONE;
DEFINE FIELD OVERWRITE chunked ON TABLE file TYPE option<string> DEFAULT NONE;

DEFINE FIELD OVERWRITE path ON file COMPUTED (
    ($this.parent.path || '') + '/' + $this.filename
) TYPE string;
-- DEFINE FIELD OVERWRITE is_folder ON TABLE file COMPUTED (
--     $this.file IS NONE AND $this.content IS NONE AND $this.symlink IS NONE
-- );

-- File content (folders are defined by leaving all of these empty)
DEFINE FIELD OVERWRITE file       ON TABLE file TYPE option<bytes> DEFAULT NONE;
DEFINE FIELD OVERWRITE content    ON TABLE file TYPE option<string> DEFAULT NONE;
DEFINE FIELD OVERWRITE symlink    ON TABLE file TYPE option<file> DEFAULT NONE;

-- Timestamps
DEFINE FIELD OVERWRITE created_at ON TABLE file TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD OVERWRITE updated_at ON TABLE file TYPE datetime VALUE time::now();
DEFINE FIELD OVERWRITE deleted_at ON TABLE file TYPE option<datetime> DEFAULT NONE;
