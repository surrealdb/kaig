REMOVE TABLE user;
REMOVE TABLE team;
REMOVE TABLE plays_for;

-- ------------------------------------------------------------
-- CRUD

CREATE user:martin CONTENT {name:"martin"};
CREATE user:ignacio CONTENT {name:"ignacio"};
CREATE user:fabian;
CREATE user:foo;

SELECT * FROM user;

UPDATE user:martin SET lastname="schaer";

DELETE user:foo;



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
-- Graph queries for packages/demo-graph

SELECT *,<-in_category<-? FROM category;

SELECT *, <-has_tag<-? FROM tag;

SELECT *,<->? FROM container;

SELECT *,->?->? FROM document;

SELECT *,
    @.{1}(->stored_in->?) AS cont1,
    @.{2}(->stored_in->?) AS cont2,
    @.{3}(->stored_in->?) AS cont3,
    @.{4}(->stored_in->?) AS cont4,
    @.{5}(->stored_in->?) AS cont5
FROM document;

-- ------------------------------------------------------------
-- Graph advanced

{
    -- REMOVE TABLE node;
    -- REMOVE TABLE edge;
    CREATE |node:1..10|;

    FOR $node IN SELECT * FROM node {
      LET $next = type::thing("node", $node.id.id() + 1);
        RELATE $node->edge->$next SET read = rand::bool();
    };
};

-- Recursive query
SELECT @.{1..6}.{
    id,
    next: ->edge[WHERE read = true]->node.@
} FROM node;



-- ------------------------------------------------------------
-- Functions

REMOVE FUNCTION fn::search;
DEFINE FUNCTION fn::search($name: String) {
    RETURN SELECT * FROM ONLY user WHERE name ~ $name LIMIT 1;
};

RETURN fn::search("martin");
