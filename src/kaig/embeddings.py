import os
from collections.abc import Sequence
from typing import Literal

import ollama
from openai import OpenAI


class Embedder:
    def __init__(
        self,
        *,
        provider: Literal["ollama", "openai"],
        model_name: str,
        vector_type: str,
    ):
        """
        Initialize embedder with specified provider.

        Params:
        ======
        - provider: "ollama" or "openai"
        - model_name: model name (e.g., "nomic-embed-text" for Ollama, "text-embedding-3-small" for OpenAI)
        - vector_type: vector type for database (e.g., "F32", "I8")
        """
        self._provider: Literal["ollama", "openai"] = provider
        self.model_name: str = model_name
        self.vector_type: str = vector_type

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

    @property
    def max_length(self) -> int:
        """Maximum token length supported for embeddings for the current provider/model."""
        if self._provider == "ollama":
            # Try to derive from local model metadata
            try:
                info = ollama.show(self.model_name)
                if isinstance(info, dict):
                    model_info = info.get("model_info") or {}  # pyright: ignore[reportUnknownVariableType]
                    if isinstance(model_info, dict):
                        for key in (
                            "num_ctx",
                            "context_length",
                            "max_context_length",
                            "ctx",
                        ):
                            val = model_info.get(key)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                            if val is not None:
                                try:
                                    return int(val)  # pyright: ignore[reportUnknownArgumentType]
                                except Exception:
                                    try:
                                        return int(str(val))  # pyright: ignore[reportUnknownArgumentType]
                                    except Exception:
                                        pass
                    params = info.get("parameters")  # pyright: ignore[reportAny]
                    if isinstance(params, str):
                        import re

                        m = re.search(r"\bnum_ctx\s+(\d+)\b", params)
                        if m:
                            return int(m.group(1))
            except Exception:
                # If we cannot inspect the model, fall back to sensible defaults for common models.
                pass

            name = self.model_name.lower()
            if "nomic-embed" in name:
                return 8192
            if "bge" in name:
                return 4096
            # Generic fallback for most models in Ollama
            return 8192
        elif self._provider == "openai":
            name = self.model_name.lower()
            # OpenAI embedding models support up to 8192 tokens
            if name in (
                "text-embedding-3-small",
                "text-embedding-3-large",
                "text-embedding-ada-002",
            ):
                return 8192
            if name.startswith("text-embedding-3-"):
                return 8192
            # Default to 8192 if unknown
            return 8192
        else:
            raise ValueError(f"Unknown provider: {self._provider}")

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
        if self._provider == "ollama":
            return self._embed_ollama(text)
        else:
            return self._embed_openai(text)

    def embed_batch(self, texts: list[str]) -> Sequence[Sequence[float]]:
        if self._provider == "ollama":
            return self._embed_batch_ollama(texts)
        else:
            return self._embed_batch_openai(texts)
