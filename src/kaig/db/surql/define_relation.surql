DEFINE TABLE OVERWRITE {name} TYPE RELATION IN {in_tb} OUT {out_tb};

DEFINE INDEX {name}_unique_idx ON {name} FIELDS {in_tb}, {out_tb} UNIQUE;
