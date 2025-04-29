import asyncio
import time

import click

from demo_graph_rag_gaming.db import DB
from demo_graph_rag_gaming.embeddings import EmbeddingsGenerator
from demo_graph_rag_gaming.pipeline import load_corpus
from demo_graph_rag_gaming.pipeline import query as query_handler


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    db = DB()
    embeddings_generator = EmbeddingsGenerator()
    ctx.obj["db"] = db
    ctx.obj["embeddings_generator"] = embeddings_generator


@cli.command()
@click.pass_context
def load(ctx):
    asyncio.run(load_corpus(ctx.obj["db"], ctx.obj["embeddings_generator"]))


@cli.command()
@click.argument("text")
@click.pass_context
def query(ctx, text):
    start_time = time.monotonic()
    asyncio.run(query_handler(ctx.obj["db"], ctx.obj["embeddings_generator"], text))
    end_time = time.monotonic()
    time_taken = end_time - start_time
    click.secho(f"Query executed in {time_taken:.2f}s", fg="black")


if __name__ == "__main__":
    cli(obj={})
