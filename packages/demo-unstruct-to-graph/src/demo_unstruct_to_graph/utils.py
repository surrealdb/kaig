import re


def is_chunk_empty(text: str) -> bool:
    cleaned_string = re.sub(r"\W+", " ", text)
    cleaned_string = cleaned_string.strip()
    return len(cleaned_string) == 0
