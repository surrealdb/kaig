PROMPT_INFER_CONCEPTS = """
Given the "TEXT" below, can you generate a list of concepts that can be used
to describe it?. Don't provide explanations.

{additional_instructions}

TEXT:
{text}
"""

PROMPT_NAME_FROM_DESC = """
Given the following item description, can you provide a short name for it in
between 2 to 10 words? Don't anything else in your answer.

DESCRIPTION:
{desc}
"""

PROMPT_INFER_ATTRIBUTES = """
Given the description below, can you generate a JSON object using the
provided schema?

Don't provide explanations.
{additional_instructions}

SCHEMA:
```
{schema}
```

DESCRIPTION:
{desc}
"""

PROMPT_ANSWER = """
{additional_instructions}

Given the following data, can you generate an answer in plain english?

QUESTION: {question}

DATA:
{data}
"""


PROMPT_SUMMARIZE = """
Summarize the following text in 1 or 2 sentences. Don't provide explanations.

{text}
"""

SENTIMENTS = ["positive", "negative", "neutral"]
PROMPT_SENTIMENT = f"""Select the sentiment that matches the text better.
SENTIMENTS: {", ".join(SENTIMENTS)}
TEXT: {{text}}
"""
