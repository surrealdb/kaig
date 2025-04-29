import asyncio
import json
import time

import click
import pandas as pd
import requests

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
@click.argument("col")
@click.argument("file")
@click.option("-l", "--limit", type=int, default=-1)
@click.option("-s", "--skip", type=int, default=-1)
@click.pass_context
def load(ctx, col, limit, skip, file):
    with open(file) as f:
        applist = json.load(f)
        # appid, name
        games = applist["applist"]["apps"]
    if skip != -1:
        games = games[skip:]
    if limit != -1:
        games = games[:limit]

    # query API for each game
    details = []
    with click.progressbar(games) as bar:
        for game in bar:
            appid = game["appid"]
            q = f"https://store.steampowered.com/api/appdetails?appids={appid}"
            res = requests.get(q)
            data = res.json()
            if data[str(appid)]["success"]:
                details.append(data[str(appid)]["data"])

    df = pd.json_normalize(details)

    asyncio.run(load_corpus(ctx.obj["db"], ctx.obj["embeddings_generator"], df, col))


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
