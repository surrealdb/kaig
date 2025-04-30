from sentence_transformers import SentenceTransformer

from demo_graph_rag_gaming.db import DB
from demo_graph_rag_gaming.utils import ensure_db_open


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
async def insert_embedding(
    appid: int,
    sentence: str,
    embedding: list[float],
    *,
    db: DB,
):
    # print(embeddings.shape)
    # similarities = model.similarity(embeddings, embeddings)
    # print(similarities)

    await db.insert_embedding(appid, embedding, sentence)
