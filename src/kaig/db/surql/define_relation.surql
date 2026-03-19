DEFINE TABLE IF NOT EXISTS {name} TYPE RELATION IN {in_tb} OUT {out_tb};

DEFINE INDEX IF NOT EXISTS {name}_unique_idx ON {name} FIELDS in, out UNIQUE;
