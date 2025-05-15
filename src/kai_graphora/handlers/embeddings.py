from sentence_transformers import SentenceTransformer


class EmbeddingsGenerator:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, text: str) -> list[float]:
        embeddings = self.model.encode(text)
        return embeddings.tolist()

    def generate_embeddings_list(self, text: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(text)
        return embeddings.tolist()
