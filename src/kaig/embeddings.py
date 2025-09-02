import ollama

# TODO: try other models
# from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name: str, vector_type: str):
        self.model_name = model_name
        vec = ollama.embed(model=self.model_name, input="hi").embeddings[0]
        self.dimension = len(vec)
        self.vector_type = vector_type

    def embed(self, text: str) -> list[float]:
        res = ollama.embed(model=self.model_name, input=text)
        return list(res.embeddings[0])
