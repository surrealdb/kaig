import click

from demo_vanilla.handlers.embeddings import EmbeddingsGenerator
from kai_graphora.db import DB


async def query(
    embeddings_generator: EmbeddingsGenerator, text: str, *, db: DB
):
    click.echo()
    click.secho("Query: ", fg="blue", nl=False)
    click.echo(text)
    click.echo()
    click.secho("Results:", fg="blue")
    query_embeddings = embeddings_generator.generate_embeddings(text)
    res = await db.query(text, query_embeddings)
    if not res:
        click.echo("No results found.")
    for result in res:
        click.secho(f"•{result['dist']:.0%} ", fg="green", nl=False)
        click.echo(f"{result['text']} ")
