import click
from sentence_transformers import SentenceTransformer

from demo_graph_rag_gaming.db import DB, EmbeddingInput
from demo_graph_rag_gaming.handlers.utils import ensure_db_open
from demo_graph_rag_gaming.models import AppData


class EmbeddingsGenerator:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, text: str) -> list[float]:
        embeddings = self.model.encode(text)
        # print("-----------------embeddings")
        # print(f"{text[:15]}...", embeddings.shape)
        return embeddings.tolist()

    def generate_embeddings_list(self, text: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(text)
        # print("-----------------embeddings")
        # print(embeddings.shape)
        return embeddings.tolist()


@ensure_db_open
async def gen_embeddings_handler(
    start_after: int, limit: int, embeddings_generator: EmbeddingsGenerator, *, db: DB
) -> int:
    # embeddings_generator: EmbeddingsGenerator = ctx.obj["embeddings_generator"]
    details: list[AppData] = await db.list_appdata(start_after, limit)
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
            embeddings.append(EmbeddingInput(detail.steam_appid, sentence, embedding))
    try:
        await db.insert_embeddings(embeddings)
    except Exception as e:
        errors.append(f"Error inserting embeddings {e}")

    # Summary
    click.echo(f"Generated embeddings for {len(embeddings)} apps")
    # Last inserted
    return details[-1].steam_appid
