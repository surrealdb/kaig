-- ------------------------------------------------------------
-- Graph queries

{
    REMOVE TABLE IF EXISTS category;
    REMOVE TABLE IF EXISTS tag;
    REMOVE TABLE IF EXISTS container;
    REMOVE TABLE IF EXISTS document;
    REMOVE TABLE IF EXISTS in_category;
    REMOVE TABLE IF EXISTS has_tag;
    REMOVE TABLE IF EXISTS stored_in;

    CREATE document:doc_1;
    CREATE document:doc_2;
    CREATE category:important;
    CREATE tag:red;
    CREATE tag:blue;
    CREATE container:parent_folder;
    CREATE container:folder_1;

    RELATE document:doc_1->in_category->category:important;

    RELATE document:doc_1->has_tag->tag:red;
    RELATE document:doc_1->has_tag->tag:blue;
    RELATE document:doc_2->has_tag->tag:red;

    RELATE container:folder_1->stored_in->container:parent_folder;
    RELATE document:doc_1->stored_in->container:folder_1;
    RELATE document:doc_2->stored_in->container:parent_folder;
};

"Docs by category:";
SELECT *, <-in_category<-document AS docs FROM category;

"Docs by tag:";
SELECT *, <-has_tag<-document AS docs FROM tag;

"Container relations:";
SELECT *, <->stored_in AS relations FROM container FETCH relations;

"Related nodes by document:";
SELECT *, ->?->? AS related FROM document;

"Recursive document path (fixed levels):";
SELECT *,
    @.{1}(->stored_in->?) AS cont1,
    @.{2}(->stored_in->?) AS cont2,
    @.{3}(->stored_in->?) AS cont3
FROM document;

"Recursive document path:";
SELECT @.{..}.{
    id,
    container: ->stored_in->container.@
} FROM document;

SELECT *, ->?->? FROM document;

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

"Recursive with filters:";
SELECT @.{1..6}.{
    id,
    next: ->edge[WHERE read = true]->node.@
} FROM node;



-- ------------------------------------------------------------
-- Collect with filter

{
    DELETE a, edge;

    CREATE a:1 SET bool = true;
    CREATE a:2 SET bool = true;
    CREATE a:3 SET bool = true;
    CREATE a:4 SET bool = false;
    CREATE a:5 SET bool = true;

    RELATE a:1->edge->a:2;
    RELATE a:2->edge->a:3;
    RELATE a:3->edge->a:4;
    RELATE a:4->edge->a:5;

    RETURN a:1.{..+collect+inclusive}
                (->edge->a[?bool]);
};
