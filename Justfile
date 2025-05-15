mod demo-example './packages/demo-games'

default:
    @just --list

db:
    surreal start -u demo -p demo rocksdb:demo.db

sql:
    surreal sql -u demo -p demo --ns demo --db demo --pretty
