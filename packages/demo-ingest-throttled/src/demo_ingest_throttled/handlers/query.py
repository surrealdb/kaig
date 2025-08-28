import click

from kai_graphora.db import DB

from ..models import AppData


async def query(text: str, *, db: DB):
    click.echo()
    click.secho("Query: ", fg="blue", nl=False)
    click.echo(text)
    click.echo()
    click.secho("Results:", fg="blue")
    query_embeddings = db.embedder.embed(text)
    res = await db.async_vector_search(AppData, query_embeddings)
    if not res:
        click.echo("No results found.")
    for result, score in res:
        click.secho(f"•{score:.0%} ", fg="green", nl=False)
        click.echo(f"{result.short_description} ")
