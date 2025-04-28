from sentence_transformers import SentenceTransformer


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
