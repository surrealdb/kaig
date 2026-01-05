LET $categories = RETURN (SELECT VALUE categories FROM appdata).flatten().distinct();

FOR $cat in $categories {
    CREATE type::thing("category", $cat.id) CONTENT {
        description: $cat.description
    }
}
