import asyncio
import time

import click

from demo_graph_rag_gaming.db import DB
from demo_graph_rag_gaming.embeddings import EmbeddingsGenerator, insert_embedding
from demo_graph_rag_gaming.ingest import load_json
from demo_graph_rag_gaming.models import AppData
from demo_graph_rag_gaming.query import query as query_handler


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    db = DB()
    embeddings_generator = EmbeddingsGenerator()
    ctx.obj["db"] = db
    ctx.obj["embeddings_generator"] = embeddings_generator


@cli.command()
@click.argument("file")
@click.option("-s", "--skip", type=int, default=-1)
@click.option("-l", "--limit", type=int, default=10)
@click.option("-e", "--error-limit", type=int, default=1)
@click.pass_context
def load(ctx, file, skip, limit, error_limit):
    """Read JSON and insert raw data into database"""
    db: DB = ctx.obj["db"]
    asyncio.run(load_json(file, skip, limit, error_limit, db=db))


@cli.command()
@click.pass_context
def gen_embeddings(ctx):
    """Generate and store embeddings"""
    embeddings_generator: EmbeddingsGenerator = ctx.obj["embeddings_generator"]
    # TODO: NEXT: get from DB
    details: list[AppData] = []
    for detail in details:
        # - Short description
        sentence = detail.short_description
        embedding = embeddings_generator.generate_embeddings(sentence)
        try:
            asyncio.run(
                insert_embedding(
                    detail.steam_appid, sentence, embedding, db=ctx.obj["db"]
                )
            )
        except Exception as e:
            click.secho(
                f"Error inserting embeddings for appid {detail.steam_appid}: {e}",
                fg="red",
            )


@cli.command()
@click.argument("text")
@click.pass_context
def query(ctx, text):
    start_time = time.monotonic()
    asyncio.run(query_handler(ctx.obj["embeddings_generator"], text, db=ctx.obj["db"]))
    end_time = time.monotonic()
    time_taken = end_time - start_time
    click.secho(f"Query executed in {time_taken:.2f}s", fg="black")


if __name__ == "__main__":
    cli(obj={})
