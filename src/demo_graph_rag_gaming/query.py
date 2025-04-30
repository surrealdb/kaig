import click

from demo_graph_rag_gaming.db import DB
from demo_graph_rag_gaming.embeddings import EmbeddingsGenerator
from demo_graph_rag_gaming.utils import ensure_db_open


@ensure_db_open
async def query(embeddings_generator: EmbeddingsGenerator, text: str, *, db: DB):
    click.secho("Query: ", fg="blue", nl=False)
    click.echo(text)
    click.secho("Results:", fg="blue")
    try:
        query_embeddings = embeddings_generator.generate_embeddings(text)
        res = await db.query(text, query_embeddings)
        for result in res:
            click.echo(f"{result['text']} ", nl=False)
            click.secho(f"({result['dist']:.2f})", fg="green")
    except Exception as e:
        raise e
    finally:
        await db.close()
