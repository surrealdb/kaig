import json
import re
import time
from typing import Any, Callable, TypeVar

import ollama
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

T = TypeVar("T", bound=BaseModel)

# TODO: add logger/signals to allow us to meassure model performance

PROMPT_NAME_FROM_DESC = """
Given the following item description, can you provide a short name for it in
between 2 to 10 words? Don't anything else in your answer.

{desc}
"""

PROMPT_INFER_ATTRIBUTES = """
Given the following description, can you generate a JSON object using the
provided schema?

Don't provide explanations.
{additional_instructions}

Schema:

```
{schema}
```

Description:

{desc}
"""

PROMPT_ANSWER = """
{additional_instructions}

Given the following data, can you generate an anwers in plain english?

The question: {question}

The data:
{data}
"""


def extract_json(text: str) -> str:
    pattern = r"```(?:json)?(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        res = matches[0]
    else:
        pattern = r"(\{.*\})"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            res = matches[0]
        else:
            res = text
    return res.strip()


class LLM:
    def __init__(
        self,
        model_name="all-MiniLM-L6-v2",
        ollama_model="llama3.2",
        *,
        analytics: Callable[[str, str, str, float, str], None] | None = None,
        tag: str | None = None,
    ):
        """
        Params:
        ======
        - model_name
        - ollama_model
        - tag: helps to group analytics data
        """
        self._sentence_transformer = SentenceTransformer(model_name)
        self._ollama_model = ollama_model
        self._analytics = analytics
        self._tag = tag if tag is not None else str(int(time.time()))
        self.dimensions = len(self.gen_embedding_from_desc("test"))

    def set_analytics(
        self, analytics: Callable[[str, str, str, float, str], None]
    ) -> None:
        self._analytics = analytics

    def gen_embedding_from_desc(self, text: str) -> list[float]:
        embeddings = self._sentence_transformer.encode(text)
        return embeddings.tolist()

    def gen_name_from_desc(self, desc: str) -> str:
        res = ollama.generate(
            model=self._ollama_model,
            prompt=PROMPT_NAME_FROM_DESC.format(desc=desc),
        )
        return res.response

    def gen_answer(
        self,
        question: str,
        data: dict[str, Any] | list[dict[str, Any]],
        additional_instructions: str = "",
    ) -> str:
        res = ollama.generate(
            model=self._ollama_model,
            prompt=PROMPT_ANSWER.format(
                data=data,
                question=question,
                additional_instructions=additional_instructions,
            ),
        )
        return res.response

    def infer_attributes(
        self,
        desc: str,
        model: type[T],
        additional_instructions: str | None = None,
        metadata: dict[str, Any] = {},
    ) -> T | None:
        prompt = PROMPT_INFER_ATTRIBUTES.format(
            desc=desc,
            schema=model.model_json_schema(),
            additional_instructions=additional_instructions,
        )
        # TODO: use format option for JSON
        res = ollama.generate(model=self._ollama_model, prompt=prompt)
        cleaned = extract_json(res.response)

        # add metadata when LLM failed to infer
        try:
            cleaned_dict = json.loads(cleaned)
            for key, value in metadata.items():
                if key not in cleaned_dict:
                    cleaned_dict[key] = value
        except Exception as e:
            print(f"Failed to parse JSON: {cleaned}. {e}")
            cleaned_dict = {}

        try:
            result = model.model_validate_json(json.dumps(cleaned_dict))
            if self._analytics:
                self._analytics(
                    "infer_attributes", prompt, res.response, 1, self._tag
                )
            return result
        except Exception as e:
            print(f"Failed to instantiate model: {cleaned}. {e}")
            if self._analytics:
                self._analytics(
                    "infer_attributes", prompt, res.response, 0, self._tag
                )
            return None
