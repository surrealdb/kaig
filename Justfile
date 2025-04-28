default:
    @just --list

run:
    # uv run main.py
    uv run demo

db:
    surreal start -u demo -p demo rocksdb:demo.db

sql:
    surreal sql -u demo -p demo --ns demo --db demo --pretty
