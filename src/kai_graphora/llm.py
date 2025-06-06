import re
from typing import TypeVar

import ollama
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

T = TypeVar("T", bound=BaseModel)

# TODO: add logger/signals to allow us to meassure model performance

PROMPT_NAME_FROM_DESC = """
Given the following item description, can you provide a short name for it in between 2 to 10 words? Don't anything else in your answer.

{desc}
"""

PROMPT_INFER_ATTRIBUTES = """
Given the following item description, can you generate a JSON object that represents that item using the provided schema? Don't provide explanations.

Schema:
```
{schema}
```

Item description:
{desc}
"""


def extract_json(text: str) -> str:
    pattern = r"```(?:json)?(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[0] if matches else text


class LLM:
    def __init__(self, model_name="all-MiniLM-L6-v2", ollama_model="llama3.2"):
        self._sentence_transformer = SentenceTransformer(model_name)
        self._ollama_model = ollama_model

    def gen_embedding_from_desc(self, text: str) -> list[float]:
        embeddings = self._sentence_transformer.encode(text)
        return embeddings.tolist()

    def gen_name_from_desc(self, desc: str) -> str:
        res = ollama.generate(
            model=self._ollama_model,
            prompt=PROMPT_NAME_FROM_DESC.format(desc=desc),
        )
        # print(f"{desc} -> {res.response}")
        return res.response

    def infer_attributes(self, desc: str, model: type[T]) -> T | None:
        res = ollama.generate(
            model=self._ollama_model,
            prompt=PROMPT_INFER_ATTRIBUTES.format(
                desc=desc, schema=model.schema_json()
            ),
        )
        # print(f"{desc} -> {res.response}")
        try:
            return model.model_validate_json(res.response.strip())
        except Exception as e:
            print(f"Failed to instantiate model: {res.response}. {e}")
            return None
