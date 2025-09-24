from dataclasses import asdict, dataclass
from textwrap import dedent

from surrealdb import RecordID

from kaig.db import DB
from kaig.db.queries import WhereClause, order_limit_start


@dataclass
class User:
    id: str | None
    username: str
    team: RecordID | None = None


def main():
    table_user = "user"
    table_notification = "notification"
    tables = [table_user, table_notification]

    # -- DB connection
    url = "ws://localhost:8000/rpc"
    db_user = "root"
    db_pass = "root"
    db_ns = "kaig"
    db_db = "demo-simple"
    db = DB(url, db_user, db_pass, db_ns, db_db, tables=tables)

    # Remove this if you don't want to clear all your tables on every run
    db.clear()

    # Only required if you have vector_tables or graph_relations in your DB
    # db.init_db()

    # These are SurrealDB's RecordIDs. We don't necessarily need a `team` table
    # and records to use them
    team_green = RecordID("team", "green")
    team_blue = RecordID("team", "blue")

    # -- Define event
    query = f"""
        DEFINE EVENT create_user ON TABLE {table_user}
            WHEN $event = "CREATE" AND $after.team = None
            THEN (
                CREATE {table_notification} SET
                    msg = "User created without a team",
                    user = $after.id,
                    created_at = time::now()
            );
    """
    _ = db.sync_conn.query(query)

    # -- Create one record
    new_user = User(id=None, username="kaig", team=team_green)
    user = db.query_one(
        f"CREATE ONLY {table_user} CONTENT $record",
        {"record": asdict(new_user)},
        User,
    )
    print(f"\n--- Created: ---\n{user}")
    # User(id=RecordID(table_name=user, record_id=vv1gmrwwq6cvw45xg4wf), username='kaig', team=RecordID(table_name=team, record_id=green))

    # Another way is using the DB connection object directly, which is the
    # SurrealDB Python SDK: https://surrealdb.com/docs/sdk/python
    #
    # doc = db.sync_conn.create(table, {"username": "kaig"})

    # -- Create many records
    new_users = [
        asdict(User(id=None, username="1", team=team_green)),
        asdict(User(id=None, username="2", team=team_blue)),
        asdict(User(id=None, username="3", team=team_blue)),
        asdict(User(id=None, username="4", team=None)),
        asdict(User(id=None, username="5", team=None)),
    ]
    _ = db.query(f"INSERT INTO {table_user} $list", {"list": new_users}, User)

    # -- Query all documents
    users = db.query(f"SELECT * FROM {table_user}", {}, User)
    print(f"\n--- All: --\n{users}")
    # [User(id=RecordID(table_name=user, record_id=25sslmmrv4p4rm4vpbw0), username='5', team=None), User(id=RecordID(table_name=user, record_id=8nbpgmkw9u438lx3g47r), username='1', team=RecordID(table_name=team, record_id=green)), User(id=RecordID(table_name=user, record_id=ifrfajan8c44cn7vjz09), username='3', team=RecordID(table_name=team, record_id=blue)), User(id=RecordID(table_name=user, record_id=rcycrch7qie3ytgd1giy), username='2', team=RecordID(table_name=team, record_id=blue)), User(id=RecordID(table_name=user, record_id=sa39vpybhmt7h4r405hb), username='4', team=None), User(id=RecordID(table_name=user, record_id=vv1gmrwwq6cvw45xg4wf), username='kaig', team=RecordID(table_name=team, record_id=green))]

    # -- Query one document
    assert user is not None
    result = db.query_one(
        "SELECT * FROM ONLY $record", {"record": user.id}, User
    )
    print(f"\n--- Query one: ---\n{result}")
    # User(id=RecordID(table_name=user, record_id=vv1gmrwwq6cvw45xg4wf), username='kaig', team=RecordID(table_name=team, record_id=green))

    # -- With filters, sort, and pagination
    where = WhereClause()
    where = where.and_("team", team_green)
    where_clause, where_vars = where.build()
    order_limit_start_clause = order_limit_start("username", "DESC", 5, 0)
    query = dedent(f"""
        SELECT *
        FROM {table_user}
        {where_clause}
        {order_limit_start_clause}
    """)
    filtered = db.query(query, where_vars, User)
    print(f"\n--- Filtered: --\n{filtered}")
    # [User(id=RecordID(table_name=user, record_id=vv1gmrwwq6cvw45xg4wf), username='kaig', team=RecordID(table_name=team, record_id=green)), User(id=RecordID(table_name=user, record_id=8nbpgmkw9u438lx3g47r), username='1', team=RecordID(table_name=team, record_id=green))]

    count = db.count(table_user, "", {})
    print(f"\n--- Total user count: {count}")

    # -- Query notifications
    notifications = db.query(f"SELECT * FROM {table_notification}", {}, dict)
    print(f"\n--- Notifications: --\n{notifications}")
    # [{'created_at': datetime.datetime(2025, 9, 24, 22, 3, 58, 899922, tzinfo=datetime.timezone.utc), 'id': RecordID(table_name=notification, record_id=gj1hpep0n8dflso4pt78), 'msg': 'User created without team', 'user': RecordID(table_name=user, record_id=sa39vpybhmt7h4r405hb)}, {'created_at': datetime.datetime(2025, 9, 24, 22, 3, 58, 899955, tzinfo=datetime.timezone.utc), 'id': RecordID(table_name=notification, record_id=i45i8n9t4qww5r9zswzp), 'msg': 'User created without team', 'user': RecordID(table_name=user, record_id=25sslmmrv4p4rm4vpbw0)}]


if __name__ == "__main__":
    main()
