from demo_unstruct_to_graph import flow

from kaig.db import DB


def test_flow():
    db = DB("mem://", "root", "root", "kaig", "test-flow")
    executor = flow.Executor(db)

    _ = db.sync_conn.query("CREATE document SET text = 'hello'")
    _ = db.sync_conn.query("CREATE document")

    @executor.flow(
        table="document", output={"field": "chunked"}, dependencies=["text"]
    )
    def chunk_flow(record: flow.Record):  # pyright: ignore[reportUnusedFunction]
        _ = db.sync_conn.query(
            "UPDATE $rec_id SET chunked = true", {"rec_id": record["id"]}
        )
        _ = db.sync_conn.query(
            "CREATE chunk SET text = $text, document = $document",
            {"text": record["text"], "document": record["id"]},
        )

    @executor.flow(table="chunk", output={"field": "meta"})
    def metadata_flow(record: flow.Record):  # pyright: ignore[reportUnusedFunction]
        _ = db.sync_conn.query(
            "UPDATE $rec_id SET meta = {time: time::now()}",
            {"rec_id": record["id"]},
        )

    res = db.query("SELECT * FROM document WHERE chunked = true", {}, dict)
    assert len(res) == 0  # pyright: ignore[reportUnknownArgumentType]

    results = executor.execute_flows_once()
    assert results["chunk_flow"] == 1
    assert results["metadata_flow"] == 0

    res = db.query("SELECT * FROM document WHERE chunked = true", {}, dict)
    assert len(res) == 1  # pyright: ignore[reportUnknownArgumentType]
    res = db.query("SELECT * FROM chunk WHERE meta IS NOT NONE", {}, dict)
    assert len(res) == 0  # pyright: ignore[reportUnknownArgumentType]

    results = executor.execute_flows_once()
    assert results["chunk_flow"] == 0
    assert results["metadata_flow"] == 1

    res = db.query("SELECT * FROM chunk WHERE meta IS NOT NONE", {}, dict)
    assert len(res) == 1  # pyright: ignore[reportUnknownArgumentType]

    results = executor.execute_flows_once()
    assert results["chunk_flow"] == 0
    assert results["metadata_flow"] == 0
