REMOVE TABLE IF EXISTS user;
REMOVE TABLE IF EXISTS team;
REMOVE TABLE IF EXISTS plays_for;

-- ------------------------------------------------------------
-- CRUD

CREATE user:martin CONTENT { name: "martin" };
CREATE user:ignacio CONTENT { name: "ignacio" };
CREATE user:fabian;
CREATE user:foo;

SELECT * FROM user;

UPDATE ONLY user:martin SET lastname = "schaer";

DELETE user:foo;

// Notes:
// - The ONLY keyword in the UPDATE above, turns the result
//   into a single object istead of being a list with a single
//   object

-- ------------------------------------------------------------
-- Relations

CREATE team:green SET name = "Green";
CREATE team:red SET name = "Red";
UPDATE user:martin SET team = team:green;

SELECT id, name, team.name FROM user;
SELECT id, name, team FROM user FETCH team;



-- ------------------------------------------------------------
-- Graph relations

RELATE user:martin->plays_for->team:green;
RELATE user:ignacio->plays_for->team:green;
RELATE user:fabian->plays_for->team:red;

SELECT *, ->plays_for->team as team FROM user;



-- ------------------------------------------------------------
-- Functions

DEFINE FUNCTION OVERWRITE fn::search($name: String) {
    RETURN SELECT * FROM ONLY user WHERE name ~ $name LIMIT 1;
};

RETURN fn::search("martin");
