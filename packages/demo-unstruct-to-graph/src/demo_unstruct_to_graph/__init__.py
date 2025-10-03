from demo_unstruct_to_graph.loaders.google_drive.download import download_file

# from demo_unstruct_to_graph.loaders.google_spreadsheet import load
from kaig.db import DB


def init_db() -> None:
    tables = ["upload", "chunk"]

    # -- DB connection
    url = "ws://localhost:8000/rpc"
    db_user = "root"
    db_pass = "root"
    db_ns = "kaig"
    db_db = "demo-unstruct-to-graph"
    db = DB(url, db_user, db_pass, db_ns, db_db, tables=tables)

    # Remove this if you don't want to clear all your tables on every run
    db.clear()

    db.init_db()


def main() -> None:
    download_file(
        "Copy of SURREALDB_ProcessUnity-Cyber-Risk-Questionnaire_2025-09-19 (4)",
        ".",
    )
