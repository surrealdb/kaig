import click

from kai_graphora.db import DB
from kai_graphora.llm import LLM


async def query(text: str, *, db: DB, llm: LLM):
    click.echo()
    click.secho("Query: ", fg="blue", nl=False)
    click.echo(text)
    click.echo()
    click.secho("Results:", fg="blue")
    query_embeddings = llm.gen_embedding_from_desc(text)
    res = await db.async_vector_search(text, query_embeddings)
    if not res:
        click.echo("No results found.")
    for result in res:
        click.secho(f"•{result['dist']:.0%} ", fg="green", nl=False)
        click.echo(f"{result['text']} ")
