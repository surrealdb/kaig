from collections.abc import Sequence

import ollama

# TODO: try other models
# from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name: str, vector_type: str):
        self.model_name: str = model_name
        vec = ollama.embed(model=self.model_name, input="hi").embeddings[0]
        self.dimension: int = len(vec)
        self.vector_type: str = vector_type

    def embed(self, text: str) -> list[float]:
        res = ollama.embed(model=self.model_name, input=text)
        return list(res.embeddings[0])

    def embed_batch(self, texts: list[str]) -> Sequence[Sequence[float]]:
        res = ollama.embed(model=self.model_name, input=texts)
        return res.embeddings
