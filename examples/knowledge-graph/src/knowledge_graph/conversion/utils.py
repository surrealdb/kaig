import hashlib
import re
import unicodedata
from pathlib import Path


def sanitize_filename(name: str) -> str:
    base = Path(name).name
    base = unicodedata.normalize("NFKD", base)
    base = base.encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    base = base.strip("._")
    if not base:
        base = "file"
    if len(base) > 80:
        stem, dot, ext = base.partition(".")
        h = hashlib.sha256(base.encode("utf-8")).hexdigest()[:8]
        stem = stem[:60]
        base = f"{stem}_{h}.{ext}" if dot else f"{stem}_{h}"
    return base
