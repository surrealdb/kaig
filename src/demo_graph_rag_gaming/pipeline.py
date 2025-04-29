import click

from .db import DB
from .embeddings import EmbeddingsGenerator


async def load_corpus(db: DB, embeddings_generator: EmbeddingsGenerator):
    await db.ensure_open()
    sentences = [
        "This is an example sentence",
        "Each sentence is converted",
        "This is really funny",
        "Jokes make people laugh",
        "Jokes are funny",
        "F1 teams are really competitive",
        "Racing drivers are athletes",
        "Driving a clown car",
        "Changing a motor's oil is a sport",
        "Baseball is played with a bat and a ball",
        "Allomancy is a magic system",
        "1 cup of chocolate",
    ]

    embeddings = embeddings_generator.generate_embeddings_list(sentences)
    # print(embeddings.shape)

    # similarities = model.similarity(embeddings, embeddings)
    # print(similarities)

    try:
        for i, embedding in enumerate(embeddings):
            await db.insert_embedding(embedding, sentences[i])
    except Exception as e:
        click.secho(f"Error inserting embeddings: {e}", fg="red")
        raise e
    finally:
        await db.close()


async def query(db: DB, embeddings_generator: EmbeddingsGenerator, text: str):
    await db.ensure_open()
    click.secho("Query: ", fg="blue", nl=False)
    click.echo(text)
    click.secho("Results:", fg="blue")
    try:
        res = await db.query(text, embeddings_generator)
        for result in res:
            click.echo(f"{result['text']} ", nl=False)
            click.secho(f"({result['dist']:.2f})", fg="green")
    except Exception as e:
        raise e
    finally:
        await db.close()
