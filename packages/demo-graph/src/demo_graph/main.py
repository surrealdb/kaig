import click

from demo_graph.handlers.ingest import ingest_things_handler
from demo_graph.handlers.query import query_handler
from kai_graphora.db import DB, Relation
from kai_graphora.llm import LLM


@click.group()
@click.option("-u", "--username", type=str, default="root")
@click.option("-p", "--password", type=str, default="root")
@click.option("--ns", type=str, default="demo-graph")
@click.option("--db", type=str, default="demo-graph")
@click.pass_context
def cli(ctx, username, password, ns, db) -> None:
    ctx.ensure_object(dict)
    click.echo("Init LLM...")
    llm = LLM()
    click.echo("Init DB...")
    db = DB(
        "ws://localhost:8000/rpc",
        username,
        password,
        ns,
        db,
        llm,
        vector_tables=["document", "tag", "category"],
        graph_relations=[
            Relation("has_tag", "document", "tag"),
            Relation("in_category", "document", "category"),
            Relation("stored_in", "document|container", "container"),
        ],
    )
    llm.set_analytics(db.insert_analytics_data)
    db.init_db()
    ctx.obj["db"] = db
    ctx.obj["llm"] = llm


@cli.command()
@click.argument("spreadsheet")
@click.pass_context
def ingest_from_spreadsheet(ctx, spreadsheet):
    db: DB = ctx.obj["db"]
    llm: LLM = ctx.obj["llm"]
    ingest_things_handler(db, llm, spreadsheet=spreadsheet)


@cli.command()
@click.argument("yaml_file")
@click.pass_context
def ingest_from_yaml(ctx, yaml_file):
    db: DB = ctx.obj["db"]
    llm: LLM = ctx.obj["llm"]
    ingest_things_handler(db, llm, yaml_file=yaml_file)


@cli.command()
@click.argument("json_bookmarks")
@click.pass_context
def ingest_from_bookmarks(ctx, json_bookmarks):
    db: DB = ctx.obj["db"]
    llm: LLM = ctx.obj["llm"]
    ingest_things_handler(db, llm, bookmarks=json_bookmarks)


@cli.command()
@click.argument("query")
@click.pass_context
def query_thing(ctx, query):
    db: DB = ctx.obj["db"]
    llm: LLM = ctx.obj["llm"]
    query_handler(db, llm, f"Where did I put my {query}")


@cli.command()
@click.argument("query")
@click.pass_context
def query_bookmark(ctx, query):
    db: DB = ctx.obj["db"]
    llm: LLM = ctx.obj["llm"]
    query_handler(
        db,
        llm,
        f"Can you find in my bookmarks: {query}",
        "You must include the `item_url` value in your answer.",
    )


if __name__ == "__main__":
    cli()
