import re
from pathlib import Path


def is_chunk_empty(text: str) -> bool:
    cleaned_string = re.sub(r"\W+", " ", text)
    cleaned_string = cleaned_string.strip()
    return len(cleaned_string) == 0


def safe_path(safe_dir: Path, source: Path) -> Path:
    base_path = Path.cwd().resolve()

    if source.name in {"", "."}:
        raise RuntimeError("Provided source path must include a file name.")

    # Normalize and validate the safe directory.
    safe_dir_candidate = safe_dir.expanduser()
    if not safe_dir_candidate.is_absolute():
        safe_dir_candidate = base_path / safe_dir_candidate
    resolved_safe_dir = safe_dir_candidate.resolve(strict=False)

    # Normalize and validate the source path.
    candidate = source.expanduser()
    if not candidate.is_absolute():
        candidate = base_path / candidate

    safe_path = candidate.resolve(strict=False)

    # Refuse path traversal / escape from the configured safe directory.
    try:
        _ = safe_path.relative_to(resolved_safe_dir)
    except ValueError:
        raise RuntimeError(
            "Refusing to process files outside the safe directory."
        )

    if safe_path.name != candidate.name:
        raise RuntimeError("Resolved path basename mismatch detected.")

    if safe_path.exists():
        if not safe_path.is_file():
            raise RuntimeError("Provided source path must be an existing file.")
    else:
        parent = safe_path.parent
        if not parent.exists() or not parent.is_dir():
            raise RuntimeError("Parent directory for source path must exist.")

    return safe_path
