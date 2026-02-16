DEFINE TABLE user SCHEMAFULL
    PERMISSIONS
        FOR select WHERE id = $auth.id,
        FOR create NONE,
        FOR update WHERE id = $auth.id,
        FOR delete NONE;

DEFINE FIELD email         ON TABLE user TYPE string ASSERT string::is_email($value);
DEFINE FIELD password_hash ON TABLE user TYPE string PERMISSIONS NONE;
DEFINE FIELD display_name  ON TABLE user TYPE option<string>;
DEFINE FIELD role          ON TABLE user TYPE string ASSERT $value IN ["user", "admin"] PERMISSIONS NONE;

DEFINE FIELD created_at    ON TABLE user TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD updated_at    ON TABLE user TYPE datetime VALUE time::now();
DEFINE FIELD deleted_at    ON TABLE user TYPE option<datetime> DEFAULT NONE;

DEFINE INDEX idx_user_email_unique ON TABLE user COLUMNS email UNIQUE;
