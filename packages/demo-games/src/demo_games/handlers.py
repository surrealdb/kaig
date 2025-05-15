import click

from kai_graphora.db import DB, EmbeddingInput
from kai_graphora.handlers.embeddings import EmbeddingsGenerator
from kai_graphora.handlers.utils import ensure_db_open

from .models import AppData


@ensure_db_open
async def gen_embeddings_handler(
    start_after: int,
    limit: int,
    embeddings_generator: EmbeddingsGenerator,
    *,
    db: DB,
) -> int:
    # embeddings_generator: EmbeddingsGenerator = ctx.obj["embeddings_generator"]
    details: list[AppData] = await db.list_documents(
        AppData, start_after, limit
    )
    errors = []
    embeddings = []
    with click.progressbar(details) as bar:
        for detail in bar:
            # - Short description
            sentence = detail.short_description
            embedding = embeddings_generator.generate_embeddings(sentence)
            # print(embeddings.shape)
            # similarities = model.similarity(embeddings, embeddings)
            # print(similarities)
            embeddings.append(
                EmbeddingInput(detail.steam_appid, sentence, embedding)
            )
    try:
        await db.insert_embeddings(embeddings)
    except Exception as e:
        errors.append(f"Error inserting embeddings {e}")

    # Summary
    click.echo(f"Generated embeddings for {len(embeddings)} apps")
    # Last inserted
    return details[-1].steam_appid
