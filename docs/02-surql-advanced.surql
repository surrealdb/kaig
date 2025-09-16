UPSERT user:martin CONTENT {name:"martin", metadata: { me: true }};
UPSERT user:ignacio CONTENT {name:"ignacio"};

-- you can use upsert without an ID too
UPSERT user SET name = "unknown";

LET $arr = ["martin", "ignacio"];
SELECT * FROM user WHERE id IN $arr.map(|$v| type::thing("user", $v));

LET $table = "user";
SELECT * FROM type::table($table);

SELECT * FROM ONLY user WHERE metadata.me = True LIMIT 1;

CREATE user:spensa CONTENT {name:"Spensa"};
CREATE user:jorgen CONTENT {name:"Jorgen"};



-- Single result
LET $user = SELECT VALUE id FROM ONLY user LIMIT 1;

RETURN record::id($user);
--> 'jorgen'

SELECT * FROM $user;
--> [{id: user:jorgen, name: 'Jorgen'}, ...]

-- Multiple results
LET $users = SELECT VALUE id FROM user;

RETURN $users.map(|$x| record::id($x));
--> ['jorgen', 'spensa']

SELECT * FROM $users;
--> [{id: user:jorgen, name: 'Jorgen'}, ...]

-- In one step
SELECT VALUE id.id() FROM user;
--> ['jorgen', 'spensa']

-- Check if a record exists
RETURN record::exists(user:jorgen);
--> true

-- Alternative
LET $record = type::thing("user", "jorgen");
RETURN $record.exists();
--> true

-- Counting
(SELECT count(id) AS count FROM user GROUP ALL)[0] OR {count: 0};
--> { count: 6 }
