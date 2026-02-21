-- -----------------------------------------------------------------------------
-- Thread
-- -----------------------------------------------------------------------------
DEFINE TABLE thread SCHEMAFULL
    PERMISSIONS
        FOR select WHERE user = $auth.id OR $auth.role = "admin",
        FOR create WHERE user = $auth.id,
        FOR update WHERE user = $auth.id,
        FOR delete WHERE user = $auth.id;

DEFINE FIELD user       ON TABLE thread TYPE record<user>;
DEFINE FIELD title      ON TABLE thread TYPE string;
DEFINE FIELD parent     ON TABLE thread TYPE option<record<message>>;

DEFINE FIELD created_at ON TABLE thread TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD updated_at ON TABLE thread TYPE datetime VALUE time::now();
DEFINE FIELD deleted_at ON TABLE thread TYPE option<datetime> DEFAULT NONE;

-- -----------------------------------------------------------------------------
-- Message
-- -----------------------------------------------------------------------------
DEFINE TABLE message SCHEMAFULL
    PERMISSIONS
        FOR select WHERE user = $auth.id OR $auth.role = "admin",
        FOR create WHERE user = $auth.id,
        FOR update WHERE user = $auth.id,
        FOR delete WHERE user = $auth.id;

DEFINE FIELD user       ON TABLE message TYPE record<user>;
DEFINE FIELD content    ON TABLE message TYPE string;
DEFINE FIELD thread     ON TABLE message TYPE record<thread>;

DEFINE FIELD created_at ON TABLE message TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD updated_at ON TABLE message TYPE datetime VALUE time::now();
DEFINE FIELD deleted_at ON TABLE message TYPE option<datetime> DEFAULT NONE;
