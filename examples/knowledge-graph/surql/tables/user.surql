# embedding field and index are created by kaig

DEFINE TABLE OVERWRITE user SCHEMAFULL
    PERMISSIONS
        FOR select FULL,
        FOR create NONE,
        FOR update WHERE id = $auth.id,
        FOR delete NONE;

DEFINE FIELD OVERWRITE name          ON TABLE user TYPE string | NONE;
DEFINE FIELD OVERWRITE email         ON TABLE user TYPE string ASSERT string::is_email($value);
DEFINE FIELD OVERWRITE password_hash ON TABLE user TYPE string PERMISSIONS NONE;
DEFINE FIELD OVERWRITE display_name  ON TABLE user TYPE option<string>;
DEFINE FIELD OVERWRITE role          ON TABLE user TYPE string ASSERT $value IN ["user", "admin"] PERMISSIONS NONE;

DEFINE FIELD OVERWRITE created_at    ON TABLE user TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD OVERWRITE updated_at    ON TABLE user TYPE datetime VALUE time::now();
DEFINE FIELD OVERWRITE deleted_at    ON TABLE user TYPE option<datetime> DEFAULT NONE;

DEFINE INDEX OVERWRITE idx_user_email_unique ON TABLE user COLUMNS email UNIQUE;
