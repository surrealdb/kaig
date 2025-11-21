import json
import os
import re
import time
from typing import Callable, Literal, TypeVar

import ollama
from openai import OpenAI, omit
from openai.types.chat.completion_create_params import ResponseFormat
from pydantic import BaseModel
from pydantic.json_schema import JsonSchemaValue

from .db.definitions import Object

T_Model = TypeVar("T_Model", bound=BaseModel)

# TODO: add logger/signals to allow us to meassure model performance

PROMPT_INFER_CONCEPTS = """
Given the "Text" below, can you generate a list of concepts that can be used
to describe it?. Don't provide explanations.

{additional_instructions}

## Text:

{text}
"""

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

Given the following data, can you generate an anwer in plain english?

The question: {question}

The data:
{data}
"""

PROMPT_SUMMARIZE = """
Given the following text, generate a summary of it in plain english. Don't provide explanations.

{text}
"""


def extract_json(text: str) -> str:
    pattern = r"```(?:json)?(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        res = matches[0]  # pyright: ignore[reportAny]
    else:
        pattern = r"(\{.*\})"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            res = matches[0]  # pyright: ignore[reportAny]
        else:
            res = text
    return res.strip()


class LLM:
    def __init__(
        self,
        provider: Literal["ollama", "openai"],
        model: str,
        *,
        temperature: float = 0.7,
        max_completion_tokens: int | None = None,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        analytics: Callable[[str, str, str, float, str], None] | None = None,
        tag: str | None = None,
    ):
        """
        Params:
        ======
        - provider: "ollama" or "openai"
        - model: model name (e.g., "llama3.2" for Ollama, "gpt-4" for OpenAI)
        - temperature: sampling temperature (0.0 to 2.0)
        - max_completion_tokens: maximum tokens to generate (None for provider default)
        - top_p: nucleus sampling parameter
        - frequency_penalty: penalize frequent tokens
        - presence_penalty: penalize repeated tokens
        - analytics: callback for analytics
        - tag: helps to group analytics data
        """
        self._provider: Literal["ollama", "openai"] = provider
        self._model: str = model
        self._temperature: float = temperature
        self._max_completion_tokens: int | None = max_completion_tokens
        self._top_p: float = top_p
        self._frequency_penalty: float = frequency_penalty
        self._presence_penalty: float = presence_penalty
        self._analytics: Callable[[str, str, str, float, str], None] | None = (
            analytics
        )
        self._tag: str = tag if tag is not None else str(int(time.time()))

        # Initialize OpenAI client if needed
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self._openai_client: OpenAI | None = OpenAI(api_key=api_key)
        else:
            self._openai_client = None

    @property
    def model(self) -> str:
        return self._model

    def set_analytics(
        self, analytics: Callable[[str, str, str, float, str], None]
    ) -> None:
        self._analytics = analytics

    def _generate_ollama(
        self,
        prompt: str,
        format: JsonSchemaValue | Literal["", "json"] | None = None,
    ) -> str:
        """Generate response using Ollama."""
        res = ollama.generate(model=self._model, prompt=prompt, format=format)
        return res.response

    def _generate_openai(
        self, prompt: str, response_format: ResponseFormat | None = None
    ) -> str:
        """Generate response using OpenAI."""
        if self._openai_client is None:
            raise ValueError("OpenAI client not initialized")

        response = self._openai_client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self._temperature,
            top_p=self._top_p,
            frequency_penalty=self._frequency_penalty,
            presence_penalty=self._presence_penalty,
            max_completion_tokens=self._max_completion_tokens
            if self._max_completion_tokens is not None
            else omit,
            response_format=response_format
            if response_format is not None
            else omit,
        )
        return response.choices[0].message.content or ""

    def gen_name_from_desc(self, desc: str) -> str:
        prompt = PROMPT_NAME_FROM_DESC.format(desc=desc)
        if self._provider == "ollama":
            return self._generate_ollama(prompt)
        else:
            return self._generate_openai(prompt)

    def gen_answer(
        self,
        question: str,
        data: Object | list[Object],
        additional_instructions: str = "",
    ) -> str:
        prompt = PROMPT_ANSWER.format(
            data=data,
            question=question,
            additional_instructions=additional_instructions,
        )
        if self._provider == "ollama":
            return self._generate_ollama(prompt)
        else:
            return self._generate_openai(prompt)

    def infer_attributes(
        self,
        desc: str,
        model: type[T_Model],
        additional_instructions: str | None = None,
        metadata: Object | None = None,
    ) -> T_Model | None:
        metadata = metadata or {}
        additional_instructions = additional_instructions or ""

        # For OpenAI, we need to explicitly request JSON in the prompt
        if self._provider == "openai":
            additional_instructions = (
                "Return a valid JSON object that matches the schema. "
                + additional_instructions
            )

        prompt = PROMPT_INFER_ATTRIBUTES.format(
            desc=desc,
            schema=model.model_json_schema(),
            additional_instructions=additional_instructions,
        )

        if self._provider == "ollama":
            response = self._generate_ollama(prompt)
        else:
            response = self._generate_openai(
                prompt, response_format={"type": "json_object"}
            )

        cleaned = extract_json(response)

        # add metadata when LLM failed to infer
        try:
            cleaned_dict = json.loads(cleaned)  # pyright: ignore[reportAny]
            for key, value in metadata.items():  # pyright: ignore[reportAny]
                if key not in cleaned_dict:
                    cleaned_dict[key] = value
        except Exception as e:
            print(f"Failed to parse JSON: {cleaned}. {e}")
            cleaned_dict = {}

        # remove empty values from lists
        for key in cleaned_dict:  # pyright: ignore[reportUnknownVariableType]
            if isinstance(cleaned_dict[key], list):
                cleaned_dict[key] = [x for x in cleaned_dict[key] if x]  # pyright: ignore[reportUnknownVariableType]

        try:
            result = model.model_validate_json(json.dumps(cleaned_dict))
            if self._analytics:
                self._analytics(
                    "infer_attributes", prompt, response, 1, self._tag
                )
            return result
        except Exception as e:
            print(f"Failed to instantiate model: {cleaned}. {e}")
            if self._analytics:
                self._analytics(
                    "infer_attributes", prompt, response, 0, self._tag
                )
            return None

    def infer_concepts(
        self, text: str, additional_instructions: str = ""
    ) -> list[str]:
        if self._provider == "ollama":
            prompt = PROMPT_INFER_CONCEPTS.format(
                text=text, additional_instructions=additional_instructions
            )
            ARRAY_OF_STRINGS: dict[str, object] = {
                "type": "array",
                "items": {"type": "string"},
            }
            response = self._generate_ollama(prompt, format=ARRAY_OF_STRINGS)
        else:
            # For OpenAI, we need to explicitly request JSON array in the prompt
            additional_instructions = (
                "Return a JSON array of strings. " + additional_instructions
            )
            prompt = PROMPT_INFER_CONCEPTS.format(
                text=text, additional_instructions=additional_instructions
            )
            response = self._generate_openai(
                prompt, response_format={"type": "json_object"}
            )

        try:
            parsed = json.loads(response)  # pyright: ignore[reportAny]
        except Exception:
            if self._analytics:
                self._analytics("infer_concepts", prompt, response, 0, "")
            return []

        cleaned: list[str] = []

        if isinstance(parsed, dict):
            # OpenAI doesn't support array as top-level JSON, so we need to parse
            # If it's wrapped in an object, try to find the array
            # parsed_obj = json.loads(response)
            # Look for an array value in the object
            new_parsed: list[str] = []
            for key, value in parsed.items():
                if isinstance(value, list):
                    new_parsed.extend([str(x).strip() for x in value])
                elif isinstance(value, str):
                    new_parsed.append(value.strip())
                elif value is None and isinstance(key, str):
                    new_parsed.append(key.strip())

            parsed = new_parsed

        if isinstance(parsed, list):
            #  clean the concepts and check if they are not empty or nonsense strings
            for x in parsed:  # pyright: ignore[reportUnknownVariableType]
                x = str(x).strip()  # pyright: ignore[reportUnknownArgumentType]

                # remove non-alphanumeric characters, but leave spaces
                alpha = re.sub(r"[^a-zA-Z0-9\s]", "", x)

                if x and len(alpha) > 3:
                    cleaned.append(x)
        else:
            if self._analytics:
                self._analytics("infer_concepts", prompt, response, 0, "")
            return []

        if self._analytics:
            self._analytics(
                "infer_concepts",
                prompt,
                response,
                1 if len(cleaned) > 1 else 0.5,
                "",
            )

        return cleaned

    def summarize(self, text: str) -> str:
        prompt = PROMPT_SUMMARIZE.format(text=text)
        if self._provider == "ollama":
            return self._generate_ollama(prompt)
        else:
            return self._generate_openai(prompt)
