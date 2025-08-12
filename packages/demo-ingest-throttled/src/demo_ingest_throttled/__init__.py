import asyncio
import time

import click

from kai_graphora.db import DB
from kai_graphora.embeddings import Embedder
from kai_graphora.llm import LLM

from .handlers.categories import populate_categories_handler
from .handlers.embeddings import gen_embeddings_handler
from .handlers.query import query as query_handler
from .ingest import load_json


@click.group()
@click.option("-u", "--username", type=str, default="demo")
@click.option("-p", "--password", type=str, default="demo")
@click.option("--ns", type=str, default="demo")
@click.option("--db", type=str, default="demo")
@click.pass_context
def cli(ctx, username, password, ns, db):
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
        Embedder("all-minilm:22m", "F32"),
        llm,
        document_table="appdata",
    )
    llm.set_analytics(db.insert_analytics_data)
    db.init_db()
    ctx.obj["db"] = db
    ctx.obj["llm"] = llm


@cli.command()
@click.argument("file")
@click.option("-s", "--skip", type=int, default=-1)
@click.option("-l", "--limit", type=int, default=10)
@click.option("-e", "--error-limit", type=int, default=1)
@click.option("-t", "--throttle", type=int, default=0)
@click.pass_context
def load(ctx, file, skip, limit, error_limit, throttle):
    """Read JSON and insert raw data into database"""
    db: DB = ctx.obj["db"]
    asyncio.run(
        load_json(file, skip, limit, error_limit, False, throttle, db=db)
    )


@cli.command()
@click.option("-s", "--start-after", type=int, default=0)
@click.option("-l", "--limit", type=int, default=100)
@click.pass_context
def gen_embeddings(ctx, start_after, limit):
    """Generate and store embeddings"""
    last_appid = asyncio.run(
        gen_embeddings_handler(start_after, limit, db=ctx.obj["db"])
    )
    click.echo(f"Last inserted: {last_appid}")


@cli.command()
@click.argument("text")
@click.pass_context
def query(ctx, text):
    start_time = time.monotonic()
    asyncio.run(query_handler(text, db=ctx.obj["db"]))
    end_time = time.monotonic()
    time_taken = end_time - start_time
    click.secho(f"\nQuery executed in {time_taken:.2f}s", fg="black")


@cli.command()
@click.pass_context
def populate_categories(ctx):
    asyncio.run(populate_categories_handler(db=ctx.obj["db"]))


if __name__ == "__main__":
    cli(obj={})
