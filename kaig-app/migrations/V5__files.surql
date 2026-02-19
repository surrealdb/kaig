DEFINE TABLE files SCHEMAFULL
    PERMISSIONS
        FOR select WHERE user = $auth.id OR $auth.role = "admin",
        FOR create WHERE user = $auth.id,
        FOR update WHERE user = $auth.id,
        FOR delete WHERE user = $auth.id;

DEFINE FIELD user       ON TABLE files TYPE record<user>;
DEFINE FIELD filename   ON TABLE files TYPE string;
DEFINE FIELD file       ON TABLE files TYPE bytes;

DEFINE FIELD created_at ON TABLE files TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD updated_at ON TABLE files TYPE datetime VALUE time::now();
DEFINE FIELD deleted_at ON TABLE files TYPE option<datetime> DEFAULT NONE;
