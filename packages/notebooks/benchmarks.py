# %% Imports -------------------------------------------------------------------
from pathlib import Path

import kagglehub
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots

from kaig.db import DB, VectorTableDefinition
from kaig.definitions import BaseDocument
from kaig.embeddings import Embedder
from kaig.llm import LLM


class Document(BaseDocument):
    user: str


# %% Config --------------------------------------------------------------------

ingest = False  # set this to True on the first run to ingest the data
limit = 700000  # this limits the amount of data ingested
model = "all-minilm:22m"
table = "document"
url = "ws://localhost:8000/rpc"
db_user = "root"
db_pass = "root"
ns = "kai"
db = "benchmarks"
vtables = [VectorTableDefinition(table, "HNSW", "COSINE")]

# -- Instances
embedder = Embedder(
    provider="ollama", model_name="all-minilm:22m", vector_type="F32"
)
llm = LLM(provider="ollama", model="llama3.2")
db = DB(url, db_user, db_pass, ns, db, embedder, llm, vector_tables=vtables)
if ingest:
    db.clear()
db.init_db()

# %% Ingestion -----------------------------------------------------------------

path = kagglehub.dataset_download("kaushiksuresh147/formula-1-trending-tweets")
path = Path(path) / "F1_tweets.csv"
data = pd.read_csv(path)
data.info()

# iterate over the data
for i, tweet in data.head(limit).iterrows():
    db.embed_and_insert(
        Document(
            content=str(tweet["text"]),
            # user=tweet["user_name"],
            user=str(tweet.get("user_name", "")),
        )
    )


# %% Benchmark -----------------------------------------------------------------

text = "Lewis Hamilton wins in Silverstone"
threshold = 0
k = 100
n = 100
hnsw_tests = [
    {"effort": 15, "threshold": threshold, "k": k},
    {"effort": 16, "threshold": threshold, "k": k},
    {"effort": 17, "threshold": threshold, "k": k},  # <-- fast (for low k's)
    {"effort": 18, "threshold": threshold, "k": k},
    {"effort": 20, "threshold": threshold, "k": k},
    {"effort": 25, "threshold": threshold, "k": k},
    {"effort": 30, "threshold": threshold, "k": k},
    {"effort": 40, "threshold": threshold, "k": k},  # <-- balanced (default)
    {"effort": 45, "threshold": threshold, "k": k},
    {"effort": 50, "threshold": threshold, "k": k},
    {"effort": 60, "threshold": threshold, "k": k},
    {"effort": 70, "threshold": threshold, "k": k},
    {"effort": 80, "threshold": threshold, "k": k},
    {"effort": 90, "threshold": threshold, "k": k},
    {"effort": 100, "threshold": threshold, "k": k},
]
for table in vtables:
    effort_axis = []
    times = []
    num_results = []
    low_scores = []
    for test in hnsw_tests:
        print(f"Table: {table} // Test: {test}")
        cnt = 0
        time_avg = 0
        low_score_avg = 0
        for i in range(n):
            res, time = db.vector_search_from_text(
                Document,
                text,
                table=table.name,
                k=test["k"],
                score_threshold=test["threshold"],
                effort=test["effort"]
                if table.index_type == "HNSW"
                else None,  # 15 works well for 0.2 threshold
            )
            time_avg += time / n
            low_score_avg += res[-1][1] / n
            cnt = len(res)
        print(f"{cnt}, avg {time_avg}, low score {low_score_avg}\n")
        effort_axis.append(test["effort"])
        times.append(time_avg)
        low_scores.append(low_score_avg)
        num_results.append(cnt)

    # Create subplot with secondary axis
    subplot_fig = make_subplots(
        shared_xaxes=True, specs=[[{"secondary_y": True}]]
    )

    df = pd.DataFrame()
    df["effort"] = effort_axis
    df["times"] = times
    df["num_results"] = num_results
    df["low_scores"] = low_scores
    df.set_index("effort", inplace=True)

    # Create individual plots for each metric
    fig1 = px.line(
        df,
        y="times",
        labels={"times": "Time (ms)", "effort": "Effort"},
        title=f"{table.name}: Time vs. Effort (st={threshold}, k={k}) / Query: {text}",
    )
    fig2 = px.line(
        df,
        y="num_results",
        labels={"num_results": "Number of Results", "effort": "Effort"},
        title=f"{table.name}: Number of Results vs. Effort (st={threshold}, k={k}) / Query: {text}",
    )
    fig3 = px.line(
        df,
        y="low_scores",
        labels={"low_scores": "Lowest Score", "effort": "Effort"},
        title=f"{table.name}: Lowest Score vs. Effort (st={threshold}, k={k}) / Query: {text}",
    )

    fig1.update_layout(xaxis_title="Effort")
    fig2.update_layout(xaxis_title="Effort")
    fig3.update_layout(xaxis_title="Effort")

    fig1.show(renderer="browser")
    fig2.show(renderer="browser")
    fig3.show(renderer="browser")
