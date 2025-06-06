import click

from demo_graph.handlers.ingest import ingest_things_handler
from kai_graphora.db import DB
from kai_graphora.llm import LLM


@click.group()
@click.option("-u", "--username", type=str, default="root")
@click.option("-p", "--password", type=str, default="root")
@click.option("--ns", type=str, default="demo-graph")
@click.option("--db", type=str, default="demo-graph")
@click.pass_context
def cli(ctx, username, password, ns, db) -> None:
    ctx.ensure_object(dict)
    db = DB("ws://localhost:8000/rpc", username, password, ns, db)
    ctx.obj["db"] = db
    llm = LLM()
    ctx.obj["llm"] = llm


@cli.command()
@click.argument("spreadsheet")
@click.pass_context
def ingest(ctx, spreadsheet):
    db: DB = ctx.obj["db"]
    llm: LLM = ctx.obj["llm"]
    ingest_things_handler(db, llm, spreadsheet)


if __name__ == "__main__":
    cli()
