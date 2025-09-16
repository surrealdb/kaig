-- ------------------------------------------------------------
-- Using variables for id, tables, relations
{
    REMOVE TABLE IF EXISTS  person;
    REMOVE TABLE IF EXISTS  object;
};

CREATE person:martin CONTENT { name: "Martin" };

LET $table = "object";
LET $content = { name: "Computer" };
LET $computer = CREATE type::table($table) CONTENT $content RETURN id;
LET $computer_id = RETURN $computer.first().id;
RETURN $computer_id;
SELECT * FROM type::table($table);

LET $content = { name: "my work pc" };
LET $relation = "owns";
RELATE person:martin->(type::table($relation))->$computer_id CONTENT $content;
