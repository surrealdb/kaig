# %% Imports -------------------------------------------------------------------
import json
import os
from pathlib import Path

from kaig.db import DB
from kaig.db.definitions import BaseDocument, VectorTableDefinition
from kaig.embeddings import Embedder
from kaig.llm import LLM


class Document(BaseDocument):
    category: str


# %% Ingestion -----------------------------------------------------------------

# -- Config
ingest = True  # set this to True on the first run to ingest the data
limit = 10  # this limits the amount of data ingested
model = "all-minilm:22m"
table = "document"
url = "ws://localhost:8000/rpc"
db_user = "root"
db_pass = "root"
ns = "kai"
db = "notebooks"
vtables = [VectorTableDefinition(table, "HNSW", "COSINE")]

# -- Instances
embedder = Embedder(model, "F32")
llm = LLM(provider="ollama", model="llama3.2")
db = DB(url, db_user, db_pass, ns, db, embedder, llm, vector_tables=vtables)
if ingest:
    db.clear()
db.init_db()

# -- Ingestion
path = Path(os.path.abspath(""))
with open(path / "data" / "data.json", "r") as f:
    data = json.load(f)  # pyright: ignore[reportAny]
    data: list[Document] = [Document.model_validate(doc) for doc in data]
if ingest:
    for doc in data[:limit]:
        _ = db.embed_and_insert(doc, table)

# %% Vector search -------------------------------------------------------------
prompt = "Siri"
res, _time = db.vector_search_from_text(
    Document, prompt, table=table, k=20, score_threshold=0.1, effort=40
)
for x, score in res:
    print(f"{score:.2%} - {x.content}")

# Output:
#
# 59.24% - Siri and Vivenna are sisters
# 16.48% - Idris is in the mountains
# 16.18% - Hallandren is surrounded by walls
