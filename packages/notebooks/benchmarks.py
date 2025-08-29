# %% Imports -------------------------------------------------------------------
from pathlib import Path

import kagglehub
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots

from kaig.db import DB, VectorTableDefinition
from kaig.db.definitions import BaseDocument
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
embedder = Embedder(model, "F32")
llm = LLM()
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

text = "Hamilton wins"
threshold = 0
k = 50
n = 200
hnsw_tests = [
    {"effort": 15, "threshold": threshold, "k": k},
    {"effort": 16, "threshold": threshold, "k": k},
    {"effort": 17, "threshold": threshold, "k": k},  # <-- fast
    {"effort": 18, "threshold": threshold, "k": k},
    {"effort": 20, "threshold": threshold, "k": k},
    {"effort": 25, "threshold": threshold, "k": k},
    {"effort": 30, "threshold": threshold, "k": k},
    {"effort": 40, "threshold": threshold, "k": k},  # <-- accurate
    {"effort": 45, "threshold": threshold, "k": k},
    {"effort": 50, "threshold": threshold, "k": k},
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

    fig1 = px.line(df, y="times", labels={"times": "Time"})
    fig2 = px.line(
        df, y="num_results", labels={"num_results": "Number of Results"}
    )
    fig3 = px.line(df, y="low_scores", labels={"low_scores": "Low Scores"})

    fig2.update_traces(yaxis="y2")
    fig3.update_traces(yaxis="y3")

    subplot_fig.add_traces(fig1.data + fig2.data + fig3.data)

    subplot_fig.update_layout(
        title=f"{table.name} st={threshold} k={k}",
        xaxis=dict(title="effort"),
        yaxis=dict(title="time"),
        yaxis2=dict(title="results", overlaying="y"),
        yaxis3=dict(
            title="low scores", overlaying="y", side="right", position=0.9
        ),
        showlegend=True,
    )

    # RECOLOR so as not to have overlapping colors
    subplot_fig.for_each_trace(
        lambda t: t.update(line=dict(color=t.marker.color))
    )

    subplot_fig.show(renderer="browser")
