-- -----------------------------------------------------------------------------
-- Thread
-- -----------------------------------------------------------------------------
DEFINE TABLE OVERWRITE thread SCHEMAFULL
    PERMISSIONS
        FOR select WHERE user = $auth.id OR $auth.role = "admin",
        FOR create WHERE user = $auth.id,
        FOR update WHERE user = $auth.id,
        FOR delete WHERE user = $auth.id;

DEFINE FIELD OVERWRITE user       ON TABLE thread TYPE record<user>;
DEFINE FIELD OVERWRITE title      ON TABLE thread TYPE string;
DEFINE FIELD OVERWRITE parent     ON TABLE thread TYPE option<record<message>>;

DEFINE FIELD OVERWRITE created_at ON TABLE thread TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD OVERWRITE updated_at ON TABLE thread TYPE datetime VALUE time::now();
DEFINE FIELD OVERWRITE deleted_at ON TABLE thread TYPE option<datetime> DEFAULT NONE;

-- -----------------------------------------------------------------------------
-- Message
-- -----------------------------------------------------------------------------
DEFINE TABLE OVERWRITE message SCHEMAFULL
    PERMISSIONS
        FOR select WHERE user = $auth.id OR $auth.role = "admin",
        FOR create WHERE user = $auth.id,
        FOR update WHERE user = $auth.id,
        FOR delete WHERE user = $auth.id;

DEFINE FIELD OVERWRITE user       ON TABLE message TYPE record<user>;
DEFINE FIELD OVERWRITE content    ON TABLE message TYPE string;
DEFINE FIELD OVERWRITE thread     ON TABLE message TYPE record<thread>;

DEFINE FIELD OVERWRITE created_at ON TABLE message TYPE datetime VALUE time::now() READONLY;
DEFINE FIELD OVERWRITE updated_at ON TABLE message TYPE datetime VALUE time::now();
DEFINE FIELD OVERWRITE deleted_at ON TABLE message TYPE option<datetime> DEFAULT NONE;
