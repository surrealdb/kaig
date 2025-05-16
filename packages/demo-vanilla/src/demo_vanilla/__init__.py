import asyncio
import time

import click

from demo_vanilla.handlers import gen_embeddings_handler
from demo_vanilla.ingest import load_json
from kai_graphora.db import DB
from kai_graphora.handlers.categories import populate_categories_handler
from kai_graphora.handlers.embeddings import EmbeddingsGenerator
from kai_graphora.handlers.query import query as query_handler


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    db = DB("ws://localhost:8000/rpc", "demo", "demo", "demo", "demo")
    embeddings_generator = EmbeddingsGenerator()
    ctx.obj["db"] = db
    ctx.obj["embeddings_generator"] = embeddings_generator


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
    embeddings_generator: EmbeddingsGenerator = ctx.obj["embeddings_generator"]
    last_appid = asyncio.run(
        gen_embeddings_handler(
            start_after, limit, embeddings_generator, db=ctx.obj["db"]
        )
    )
    click.echo(f"Last inserted: {last_appid}")


@cli.command()
@click.argument("text")
@click.pass_context
def query(ctx, text):
    start_time = time.monotonic()
    asyncio.run(
        query_handler(ctx.obj["embeddings_generator"], text, db=ctx.obj["db"])
    )
    end_time = time.monotonic()
    time_taken = end_time - start_time
    click.secho(f"\nQuery executed in {time_taken:.2f}s", fg="black")


@cli.command()
@click.pass_context
def populate_categories(ctx):
    asyncio.run(populate_categories_handler(db=ctx.obj["db"]))


if __name__ == "__main__":
    cli(obj={})
