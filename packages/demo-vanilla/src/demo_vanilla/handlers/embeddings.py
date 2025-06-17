import click

from demo_vanilla.models import AppData
from kai_graphora.db import DB, EmbeddingInput
from kai_graphora.llm import LLM


async def gen_embeddings_handler(
    start_after: int, limit: int, *, db: DB, llm: LLM
) -> int:
    details: list[AppData] = await db.list_documents(
        AppData, start_after, limit
    )
    errors = []
    embeddings = []
    with click.progressbar(details) as bar:
        for detail in bar:
            # - Short description
            sentence = detail.short_description
            embedding = llm.gen_embedding_from_desc(sentence)
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
