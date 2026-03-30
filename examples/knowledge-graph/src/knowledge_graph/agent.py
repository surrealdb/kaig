import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import logfire
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from surrealdb import RecordID, Value

from kaig.db import DB
from kaig.db.utils import query
from kaig.definitions import OriginalDocument

from .db import init_kaig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
stdout = logging.StreamHandler(stream=sys.stdout)
stdout.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(stdout)

db_url = os.environ.get("SURREALDB_URL", "ws://localhost:8000")
db_ns = os.environ.get("SURREALDB_NAMESPACE", "test")
db_name = os.environ.get("SURREALDB_DATABASE", "test")

# SurQL files
surql_path = (
    Path(__file__).parent.parent.parent / "surql" / "search_chunks.surql"
    # Path(__file__).parent.parent.parent / "surql" / "search_concepts.surql"
)
with open(surql_path, "r") as file:
    search_surql = file.read()


@dataclass
class Deps:
    db: DB
    openai: AsyncOpenAI


@dataclass
class ResultChunk:
    id: str
    score: float
    chunk_index: int
    content: str


@dataclass
class DocHandle:
    id: str
    filename: str
    content_type: str


@dataclass
class FileEntry:
    id: RecordID
    path: str
    content_type: str
    content: str | None = None


@dataclass
class SearchResult:
    doc: DocHandle
    best_score: float
    chunks: list[ResultChunk]


agent = Agent(
    "openai:gpt-5-mini-2025-08-07",
    deps_type=Deps,
    instructions=(
        "You are a helpful assistant that organizes my thoughts, conversations, notes, into a well-structured text file system."
        "Every time you learn something about my preferences, store it in a file in the /preferences folder. For example, create files like /preferences/food.md, /preferences/music.md, /preferences/books.md, etc."
        "When I talk about a project or task, organize the notes and current to-do list in a /project/<project_name> folder. For example, /project/social_media/2026/post_calendar_january.md or /project/support/solutions/vector_index.md"
        "Write your main notes in /notes.md, and read them every time we interact."
        "Before you answer, consider updating the /notes.md file with your latest thoughts and insights."
        "Base your answers on retrieved documents using the `retrieve` tool, keep your answers concise, and include the document name in the answer."
    ),
)


@agent.tool
async def retrieve(context: RunContext[Deps], search_query: str) -> str:
    """Retrieve documents from the user's knowledge base based on a search query.

    Args:
        search_query: The search query.
    """
    db = context.deps.db

    with logfire.span(
        "vector+graph search for {search_query=}", search_query=search_query
    ):
        if db.embedder is None:
            raise ValueError("Embedder is not configured")

        embedding = db.embedder.embed(search_query)
        results = query(
            db.sync_conn,
            search_surql,
            {"embedding": cast(Value, embedding), "threshold": 0.4},
            SearchResult,
        )

    results = "\n\n".join(
        f"# Document name: {x.doc.filename}\n{'\n\n'.join(str(y.content) for y in x.chunks)}\n"
        for x in results
    )
    # logger.debug("Retrieved data: %s", results)
    return results


class CatArgs(BaseModel):
    path: str = Field(..., description="File to read")


@agent.tool
async def cat(
    context: RunContext[Deps],
    args: CatArgs,
) -> str:
    """
    Read the full contents of a file and return it as text.

    Usage: provide an absolute path or one relative to the current working directory.
    Errors: returns an error when the path does not exist or targets a directory.
    """
    if not args.path.startswith("/"):
        args.path = "/" + args.path

    result = context.deps.db.query_one(
        "SELECT * FROM ONLY file WHERE path = $path LIMIT 1",
        {"path": args.path},
        OriginalDocument,
    )
    if result is None:
        return f"File not found: {args.path}"
    return (
        result.content
        or f"Error: content type is not text/plain {result.content_type}"
    )


@agent.tool
async def ls(
    context: RunContext[Deps],
    *,
    path: str = "/",
    all: bool = False,
    long: bool = False,
    recursive: bool = False,
    dir_only: bool = False,
    human: bool = False,
) -> str:
    """
    List entries in SurrealFs with optional recursion and size details.

    Usage: set `path` absolute or relative; `all` shows dotfiles; `long` adds byte sizes; `recursive` descends directories; `dir_only` filters to directories; `human` reports base-1024 sizes.
    """
    # Normalize prefix: must start and end with "/"
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path = path + "/"

    entries = context.deps.db.query(
        "SELECT id, path, content_type, content FROM file WHERE string::starts_with(path, $prefix)",
        {"prefix": path},
        FileEntry,
    )

    if not entries:
        return "(empty)"

    def _fmt_size(n: int) -> str:
        if not human:
            return str(n)
        for unit in ("B", "K", "M", "G", "T"):
            if n < 1024:
                return f"{n}{unit}"
            n //= 1024
        return f"{n}P"

    if recursive:
        lines: list[str] = []
        for e in entries:
            rel = e.path[len(path) :]
            if not all and any(seg.startswith(".") for seg in rel.split("/")):
                continue
            if dir_only:
                continue  # no directories in flat file store
            if long:
                size = len(e.content) if e.content else 0
                lines.append(f"{_fmt_size(size):>8}  {e.path}")
            else:
                lines.append(e.path)
        return "\n".join(lines) if lines else "(empty)"

    # Non-recursive: show only immediate children (files and "directories")
    seen_dirs: set[str] = set()
    file_lines: list[str] = []
    dir_lines: list[str] = []

    for e in entries:
        rel = e.path[len(path) :]  # relative path under prefix
        if not rel:
            continue
        slash_pos = rel.find("/")
        if slash_pos == -1:
            # Direct child file
            name = rel
            if not all and name.startswith("."):
                continue
            if dir_only:
                continue
            if long:
                size = len(e.content) if e.content else 0
                file_lines.append(f"{_fmt_size(size):>8}  {name}")
            else:
                file_lines.append(name)
        else:
            # Child in a subdirectory
            dirname = rel[:slash_pos] + "/"
            if not all and dirname.startswith("."):
                continue
            if dirname in seen_dirs:
                continue
            seen_dirs.add(dirname)
            if long:
                dir_lines.append(f"{'':>8}  {dirname}")
            else:
                dir_lines.append(dirname)

    result = sorted(dir_lines) + sorted(file_lines)
    return "\n".join(result) if result else "(empty)"


class WriteFileArgs(BaseModel):
    path: str = Field(..., description="Destination path")
    content: str = Field(..., description="File contents to write")


@agent.tool
async def write_file(context: RunContext[Deps], args: WriteFileArgs) -> str:
    """
    Write markdown content to the given path, creating or replacing the file.

    Usage: provide `path` absolute or relative; `content` is written exactly as supplied. Missing parent directories are created automatically.
    Notes: overwrites existing files.
    """
    path = args.path
    if not path.startswith("/"):
        path = "/" + path

    filename = path.rsplit("/", 1)[-1]
    parent_path = path.rsplit("/", 1)[0] or "/"
    parent_rec_id: RecordID | None = None

    # Ensure all ancestor directories exist, creating them if necessary
    if parent_path != "/":
        segments = [s for s in parent_path.split("/") if s]
        current_parent_id: RecordID | None = None
        for i, segment in enumerate(segments):
            partial_path = "/" + "/".join(segments[: i + 1])
            existing_dir = context.deps.db.query(
                "SELECT id, path, content_type FROM file WHERE path = $path",
                {"path": partial_path},
                FileEntry,
            )
            if existing_dir:
                if existing_dir[0].content_type != "folder":
                    raise ValueError(
                        f"Path already exists as a file: {partial_path}"
                    )
                current_parent_id = existing_dir[0].id
            else:
                _ = context.deps.db.sync_conn.query(
                    "CREATE file CONTENT $content",
                    {
                        "content": {
                            "filename": segment,
                            "content_type": "folder",
                            "parent": current_parent_id,
                        }
                    },
                )
                new_dir = context.deps.db.query(
                    "SELECT id, path, content_type FROM file WHERE path = $path",
                    {"path": partial_path},
                    FileEntry,
                )
                current_parent_id = new_dir[0].id

        parent_rec_id = current_parent_id

    # Check if path already exists
    existing = context.deps.db.query(
        "SELECT id, path, content_type FROM file WHERE path = $path",
        {"path": path},
        FileEntry,
    )

    if existing:
        if existing[0].content_type == "folder":
            raise IsADirectoryError(f"Path is a directory: {path}")
        _ = context.deps.db.sync_conn.query(
            "UPDATE file SET content = $content, flow_chunked = NONE, flow_keywords = NONE, updated_at = time::now() WHERE path = $path",
            {"path": path, "content": args.content},
        )
        _ = context.deps.db.sync_conn.query(
            "DELETE chunk WHERE doc = $doc",
            {"doc": existing[0].id},
        )
        return f"Updated: {path}"
    else:
        res = context.deps.db.sync_conn.query(
            "CREATE file CONTENT $content",
            {
                "content": {
                    "filename": filename,
                    "parent": parent_rec_id,
                    "content_type": "text/markdown",
                    "content": args.content,
                }
            },
        )
        logger.debug(f"Created file: {res}")
        return f"Created: {path}"


class EditArgs(BaseModel):
    path: str = Field(..., description="File to edit")
    old: str = Field(..., description="Substring or pattern to replace")
    new: str = Field(..., description="Replacement text")
    replace_all: bool = Field(
        False,
        description="Replace all occurrences (default replaces first only)",
    )


@agent.tool
async def edit(ctx: RunContext[Deps], *, args: EditArgs) -> str:
    """
    Replace text inside a SurrealFs file. Provide the target path, the text to find, and the replacement text. Set `replace_all` to true to replace every occurrence; otherwise only the first match is replaced.

    Usage:
    - `path`: absolute or relative to the current working directory inside SurrealFs.
    - `old`: substring or pattern to replace.
    - `new`: replacement text.
    - `replace_all`: boolean, default false.

    Common errors:
    - Path does not exist or points to a directory.
    - No occurrence of `old` found (operation may return unchanged content).
    """
    path = args.path
    if not path.startswith("/"):
        path = "/" + path

    existing = ctx.deps.db.query(
        "SELECT id, path, content_type, content FROM file WHERE path = $path",
        {"path": path},
        FileEntry,
    )

    if not existing:
        raise FileNotFoundError(f"File not found: {path}")
    if existing[0].content_type == "folder":
        raise IsADirectoryError(f"Path is a directory: {path}")

    current = existing[0].content or ""
    if args.old not in current:
        raise ValueError(f"Text not found in {path}: {args.old!r}")

    if args.replace_all:
        updated = current.replace(args.old, args.new)
    else:
        updated = current.replace(args.old, args.new, 1)

    file_id = existing[0].id
    _ = ctx.deps.db.sync_conn.query(
        "UPDATE file SET content = $content, flow_chunked = NONE, flow_keywords = NONE, updated_at = time::now() WHERE path = $path",
        {"path": path, "content": updated},
    )
    _ = ctx.deps.db.sync_conn.query(
        "DELETE chunk WHERE doc = $doc",
        {"doc": file_id},
    )
    return f"Edited: {path}"


class MkdirArgs(BaseModel):
    path: str = Field(
        ..., description="Directory path to create (parents included)"
    )
    parents: bool = Field(
        False, description="Create parent directories as needed"
    )


@agent.tool
async def mkdir(ctx: RunContext[Deps], *, args: MkdirArgs) -> str:
    """
    Create a directory and any missing parent directories.

    Usage: pass the desired path, absolute or relative to the current working directory.
    Errors: fails if the path already exists as a file.
    """
    path = args.path
    if not path.startswith("/"):
        path = "/" + path
    path = path.rstrip("/") or "/"

    if path == "/":
        return "/"

    segments = [s for s in path.split("/") if s]
    created: list[str] = []
    current_parent_id: RecordID | None = None

    for i, segment in enumerate(segments):
        partial_path = "/" + "/".join(segments[: i + 1])
        is_last = i == len(segments) - 1

        existing = ctx.deps.db.query(
            "SELECT id, path, content_type FROM file WHERE path = $path",
            {"path": partial_path},
            FileEntry,
        )

        if existing:
            if existing[0].content_type != "folder":
                raise ValueError(
                    f"Path already exists as a file: {partial_path}"
                )
            current_parent_id = existing[0].id
        else:
            if not is_last and not args.parents:
                raise FileNotFoundError(
                    f"Parent directory does not exist: {partial_path}. Pass parents=true to create it."
                )
            _ = ctx.deps.db.sync_conn.query(
                "CREATE file CONTENT $content",
                {
                    "content": {
                        "filename": segment,
                        "content_type": "folder",
                        "parent": current_parent_id,
                    }
                },
            )
            created.append(partial_path)
            new_dir = ctx.deps.db.query(
                "SELECT id FROM file WHERE path = $path",
                {"path": partial_path},
                FileEntry,
            )
            current_parent_id = new_dir[0].id

    if created:
        return "Created: " + ", ".join(created)
    return f"Directory already exists: {path}"


openai = AsyncOpenAI()

_ = logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()
logfire.instrument_surrealdb()
_ = logfire.instrument_openai(openai)


db = init_kaig(url=db_url, ns=db_ns, db=db_name)

# Agent chat UI
app = agent.to_web(deps=Deps(db=db, openai=openai))
