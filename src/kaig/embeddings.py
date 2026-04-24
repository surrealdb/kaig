import logging
import os
from collections.abc import Sequence
from typing import Literal

import ollama
from openai import OpenAI

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(
        self,
        *,
        provider: Literal["ollama", "openai"],
        model_name: str,
        vector_type: str,
        safe_max_chars: int = 1000,
    ):
        """
        Initialize embedder with specified provider.

        Params:
        ======
        - provider: "ollama" or "openai"
        - model_name: model name (e.g., "nomic-embed-text" for Ollama, "text-embedding-3-small" for OpenAI)
        - vector_type: vector type for database (e.g., "F32", "I8")
        - safe_max_chars: if embedding fails, we'll clip the text to this many characters and try again
        """
        self._provider: Literal["ollama", "openai"] = provider
        self.model_name: str = model_name
        self.vector_type: str = vector_type
        self.safe_max_chars: int = safe_max_chars

        # Initialize OpenAI client if needed
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self._openai_client: OpenAI | None = OpenAI(api_key=api_key)
        else:
            self._openai_client = None

        # Detect dimension by embedding a test string
        if provider == "ollama":
            vec = ollama.embed(model=self.model_name, input="hi").embeddings[0]
            self.dimension: int = len(vec)
        else:
            if self._openai_client is None:
                raise ValueError("OpenAI client not initialized")
            response = self._openai_client.embeddings.create(
                model=self.model_name, input="hi"
            )
            self.dimension = len(response.data[0].embedding)

    def _embed_ollama(self, text: str) -> list[float]:
        """Generate embedding using Ollama."""
        res = ollama.embed(model=self.model_name, input=text, truncate=True)
        return list(res.embeddings[0])

    def _embed_openai(self, text: str) -> list[float]:
        """Generate embedding using OpenAI."""
        if self._openai_client is None:
            raise ValueError("OpenAI client not initialized")

        response = self._openai_client.embeddings.create(
            model=self.model_name, input=text
        )
        return response.data[0].embedding

    def _embed_batch_ollama(
        self, texts: list[str]
    ) -> Sequence[Sequence[float]]:
        """Generate batch embeddings using Ollama."""
        res = ollama.embed(model=self.model_name, input=texts, truncate=True)
        return res.embeddings

    def _embed_batch_openai(
        self, texts: list[str]
    ) -> Sequence[Sequence[float]]:
        """Generate batch embeddings using OpenAI."""
        if self._openai_client is None:
            raise ValueError("OpenAI client not initialized")

        response = self._openai_client.embeddings.create(
            model=self.model_name, input=texts
        )
        return [data.embedding for data in response.data]

    def embed(self, text: str) -> list[float]:
        while True:
            try:
                if self._provider == "ollama":
                    return self._embed_ollama(text)
                else:
                    return self._embed_openai(text)
            except Exception as e:
                if "the input length exceeds the context length" in str(e):
                    # retry
                    text = text[: self.safe_max_chars]
                    logger.info("Retry embedding chunk, clipped to 1000 chars")
                    continue
                logger.error(
                    f"Error embedding doc with len={len(text)}: {type(e)} {e}"
                )
                raise e

    def embed_batch(self, texts: list[str]) -> Sequence[Sequence[float]]:
        if self._provider == "ollama":
            return self._embed_batch_ollama(texts)
        else:
            return self._embed_batch_openai(texts)
