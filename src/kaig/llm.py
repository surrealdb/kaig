import json
import re
import time
from typing import Callable, TypeVar

import ollama
from pydantic import BaseModel

from .db.definitions import Object

T_Model = TypeVar("T_Model", bound=BaseModel)

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
        ollama_model: str = "llama3.2",
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
        self._ollama_model: str = ollama_model
        self._analytics: Callable[[str, str, str, float, str], None] | None = (
            analytics
        )
        self._tag: str = tag if tag is not None else str(int(time.time()))

    def set_analytics(
        self, analytics: Callable[[str, str, str, float, str], None]
    ) -> None:
        self._analytics = analytics

    def gen_name_from_desc(self, desc: str) -> str:
        res = ollama.generate(
            model=self._ollama_model,
            prompt=PROMPT_NAME_FROM_DESC.format(desc=desc),
        )
        return res.response

    def gen_answer(
        self,
        question: str,
        data: Object | list[Object],
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
        model: type[T_Model],
        additional_instructions: str | None = None,
        metadata: Object | None = None,
    ) -> T_Model | None:
        metadata = metadata or {}
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

        # remove empty values from lists
        for key in cleaned_dict:
            if isinstance(cleaned_dict[key], list):
                cleaned_dict[key] = [x for x in cleaned_dict[key] if x]

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
