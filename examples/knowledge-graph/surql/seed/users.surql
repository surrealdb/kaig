UPSERT user:alice SET
    name = "Alice Chen",
    email = "alice.chen@example.com",
    password_hash = crypto::argon2::generate("alice-password"),
    display_name = "Alice",
    role = "user";

UPSERT user:bob SET
    name = "Bob Martinez",
    email = "bob.martinez@example.com",
    password_hash = crypto::argon2::generate("bob-password"),
    display_name = "Bob",
    role = "user";

UPSERT user:carol SET
    name = "Carol Johnson",
    email = "carol.johnson@example.com",
    password_hash = crypto::argon2::generate("carol-password"),
    display_name = "Carol",
    role = "user";

UPSERT user:dave SET
    name = "Dave Kim",
    email = "dave.kim@example.com",
    password_hash = crypto::argon2::generate("dave-password"),
    display_name = "Dave",
    role = "user";

UPSERT user:eve SET
    name = "Eve Patel",
    email = "eve.patel@example.com",
    password_hash = crypto::argon2::generate("eve-password"),
    display_name = "Eve",
    role = "user";
