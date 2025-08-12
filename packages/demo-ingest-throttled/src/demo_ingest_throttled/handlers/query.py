import click

from kai_graphora.db import DB


async def query(text: str, *, db: DB):
    click.echo()
    click.secho("Query: ", fg="blue", nl=False)
    click.echo(text)
    click.echo()
    click.secho("Results:", fg="blue")
    query_embeddings = db.embedder.embed(text)
    res = await db.async_vector_search(
        query_embeddings, table="appdata_embeddings"
    )
    if not res:
        click.echo("No results found.")
    for result in res:
        click.secho(f"•{result['dist']:.0%} ", fg="green", nl=False)
        click.echo(f"{result['text']} ")
