DEFINE TABLE OVERWRITE PARENT SCHEMAFULL TYPE relation PERMISSIONS
    FOR select WHERE in.owner = $auth.id OR $auth.role = "admin",
    FOR create WHERE in.owner = $auth.id,
    FOR update WHERE in.owner = $auth.id,
    FOR delete WHERE in.owner = $auth.id;
DEFINE FIELD OVERWRITE in ON TABLE PARENT TYPE record<file>;
DEFINE FIELD OVERWRITE out ON TABLE PARENT TYPE record<file>;

DEFINE TABLE OVERWRITE file SCHEMAFULL
    PERMISSIONS
        FOR select WHERE owner = $auth.id OR $auth.role = "admin",
        FOR create WHERE owner = $auth.id,
        FOR update WHERE owner = $auth.id,
        FOR delete WHERE owner = $auth.id;

DEFINE FIELD OVERWRITE owner ON TABLE file TYPE record<user>;
DEFINE FIELD OVERWRITE filename ON TABLE file TYPE string;

DEFINE FIELD OVERWRITE path ON TABLE file COMPUTED (
    array::reverse(
        $this.{..+collect}(->PARENT->file).filename
    ).join('/')
);
DEFINE FIELD OVERWRITE is_folder ON TABLE file COMPUTED (
    $this.file IS NONE AND $this.content IS NONE AND $this.symlink IS NONE
);

-- File content (folders are defined by leaving all of these empty)
DEFINE FIELD OVERWRITE file       ON TABLE file TYPE option<bytes> DEFAULT NONE;
DEFINE FIELD OVERWRITE content    ON TABLE file TYPE option<string> DEFAULT NONE;
DEFINE FIELD OVERWRITE symlink    ON TABLE file TYPE option<file> DEFAULT NONE;

-- Timestamps
DEFINE FIELD OVERWRITE created_at ON TABLE file TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD OVERWRITE updated_at ON TABLE file TYPE datetime VALUE time::now();
DEFINE FIELD OVERWRITE deleted_at ON TABLE file TYPE option<datetime> DEFAULT NONE;
