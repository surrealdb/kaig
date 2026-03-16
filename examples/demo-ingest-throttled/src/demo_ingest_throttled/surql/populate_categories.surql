LET $categories = RETURN (SELECT VALUE categories FROM appdata).flatten().distinct();

FOR $cat in $categories {
    CREATE type::record("category", $cat.id) CONTENT {
        description: $cat.description
    }
}
