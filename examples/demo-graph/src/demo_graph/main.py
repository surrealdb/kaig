import click

from demo_graph.handlers.ingest import ingest_things_handler
from demo_graph.handlers.query import query_handler
from kaig.db import DB
from kaig.definitions import Relation, VectorTableDefinition
from kaig.embeddings import Embedder
from kaig.llm import LLM


@click.group()
@click.option("-u", "--username", type=str, default="root")
@click.option("-p", "--password", type=str, default="root")
@click.option("--ns", type=str, default="demo-graph")
@click.option("--db", type=str, default="demo-graph")
@click.pass_context
def cli(
    ctx: click.Context, username: str, password: str, ns: str, db: str
) -> None:
    _ = ctx.ensure_object(dict)
    click.echo("Init LLM...")
    llm = LLM(provider="ollama", model="llama3.2")
    click.echo("Init DB...")
    embedder = Embedder(
        provider="ollama", model_name="all-minilm:22m", vector_type="F32"
    )
    _db = DB(
        "ws://localhost:8000/rpc",
        username,
        password,
        ns,
        db,
        embedder,
        llm,
        vector_tables=[
            VectorTableDefinition("document", "HNSW", "COSINE"),
            VectorTableDefinition("tag", "HNSW", "COSINE"),
            VectorTableDefinition("category", "HNSW", "COSINE"),
        ],
        graph_relations=[
            Relation("has_tag", "document", "tag"),
            Relation("in_category", "document", "category"),
            Relation("stored_in", "document|container", "container"),
        ],
    )
    llm.set_analytics(_db.insert_analytics_data)
    _db.init_db()
    ctx.obj["db"] = _db
    ctx.obj["llm"] = llm


@cli.command()
@click.argument("spreadsheet")
@click.pass_context
def ingest_from_spreadsheet(ctx: click.Context, spreadsheet: str):
    db: DB = ctx.obj["db"]
    llm: LLM = ctx.obj["llm"]
    ingest_things_handler(db, llm, spreadsheet=spreadsheet)


@cli.command()
@click.argument("yaml_file")
@click.pass_context
def ingest_from_yaml(ctx: click.Context, yaml_file: str):
    db: DB = ctx.obj["db"]
    llm: LLM = ctx.obj["llm"]
    ingest_things_handler(db, llm, yaml_file=yaml_file)


@cli.command()
@click.argument("json_bookmarks")
@click.pass_context
def ingest_from_bookmarks(ctx: click.Context, json_bookmarks: str):
    db: DB = ctx.obj["db"]
    llm: LLM = ctx.obj["llm"]
    ingest_things_handler(db, llm, bookmarks=json_bookmarks)


@cli.command()
@click.argument("query")
@click.pass_context
def query_thing(ctx: click.Context, query: str):
    db: DB = ctx.obj["db"]
    llm: LLM = ctx.obj["llm"]
    query_handler(db, llm, f"Where did I put my {query}")


@cli.command()
@click.argument("query")
@click.pass_context
def query_bookmark(ctx: click.Context, query: str):
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
