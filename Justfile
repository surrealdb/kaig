default:
    @just --list

db:
    surreal start -u demo -p demo rocksdb:demo.db

sql:
    surreal sql -u demo -p demo --ns demo --db demo --pretty

query *ARGS:
    uv run cli query "{{ARGS}}"

load:
    uv run cli load
