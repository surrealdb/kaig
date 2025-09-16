-- ------------------------------------------------------------
-- Graph queries

// TODO: add data for these queries

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
-- Recursive query

{
    REMOVE TABLE IF EXISTS node;
    REMOVE TABLE IF EXISTS edge;
    CREATE |node:1..10|;

    FOR $node IN SELECT * FROM node {
      LET $next = type::thing("node", $node.id.id() + 1);
        RELATE $node->edge->$next SET read = rand::bool();
    };
};

SELECT @.{1..6}.{
    id,
    next: ->edge[WHERE read = true]->node.@
} FROM node;



-- ------------------------------------------------------------
-- Collect with filter

{
    delete a, edge;

    create a:1 set bool = true;
    create a:2 set bool = true;
    create a:3 set bool = true;
    create a:4 set bool = false;
    create a:5 set bool = true;

    relate a:1->edge->a:2;
    relate a:2->edge->a:3;
    relate a:3->edge->a:4;
    relate a:4->edge->a:5;

    return a:1.{..+collect+inclusive}
                (->edge->a[?bool]);
};
