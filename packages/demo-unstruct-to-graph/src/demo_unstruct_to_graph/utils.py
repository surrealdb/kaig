import re
from pathlib import Path


def is_chunk_empty(text: str) -> bool:
    cleaned_string = re.sub(r"\W+", " ", text)
    cleaned_string = cleaned_string.strip()
    return len(cleaned_string) == 0


def resolve_source_path(source: Path) -> Path:
    resolved = source.expanduser().resolve()
    cwd = Path.cwd().resolve()
    try:
        _ = resolved.relative_to(cwd)
    except ValueError:
        raise RuntimeError(
            "Refusing to process files outside the working directory."
        )
    if not resolved.is_file():
        raise RuntimeError("Provided source path must be an existing file.")
    return resolved
