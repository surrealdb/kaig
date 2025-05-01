default:
    @just --list

db:
    surreal start -u demo -p demo rocksdb:demo.db

sql:
    surreal sql -u demo -p demo --ns demo --db demo --pretty

query *ARGS:
    uv run cli query "{{ARGS}}"

load limit file:
    uv run cli load -l {{limit}} -s 0 -e 10 {{file}}

gen-embeddings limit start_after="0":
    uv run cli gen-embeddings -l {{limit}} -s {{start_after}}
