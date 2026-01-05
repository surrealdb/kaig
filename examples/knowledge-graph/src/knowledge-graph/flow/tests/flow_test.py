from kaig.db import DB

from .. import Executor, Record


def test_flow():
    db = DB("mem://", "root", "root", "kaig", "test-flow")
    exe = Executor(db)

    _ = db.sync_conn.query("CREATE document SET text = 'hello'")
    _ = db.sync_conn.query("CREATE document")

    # Forced priorities just to test that on the first run metadata_flow does
    # not process any records
    @exe.flow(
        table="document",
        output={"field": "chunked"},
        dependencies=["text"],
        priority=1,
    )
    def chunk_flow(record: Record, _hash: int):  # pyright: ignore[reportUnusedFunction]
        # create chunk
        _ = db.sync_conn.query(
            "CREATE chunk SET text = $text, document = $document",
            {"text": record["text"], "document": record["id"]},
        )
        # set output field so it's not reprocessed again
        _ = db.sync_conn.query(
            "UPDATE $rec_id SET chunked = true", {"rec_id": record["id"]}
        )

    @exe.flow(table="chunk", output={"field": "meta"}, priority=2)
    def metadata_flow(record: Record, _hash: int):  # pyright: ignore[reportUnusedFunction]
        # set output field so it's not reprocessed again
        _ = db.sync_conn.query(
            "UPDATE $rec_id SET meta = {time: time::now()}",
            {"rec_id": record["id"]},
        )

    res = db.query("SELECT * FROM document WHERE chunked = true", {}, dict)
    assert len(res) == 0  # pyright: ignore[reportUnknownArgumentType]

    results = exe.execute_flows_once()
    assert results["chunk_flow"] == 1
    assert results["metadata_flow"] == 0

    res = db.query("SELECT * FROM document WHERE chunked = true", {}, dict)
    assert len(res) == 1  # pyright: ignore[reportUnknownArgumentType]
    res = db.query("SELECT * FROM chunk WHERE meta IS NOT NONE", {}, dict)
    assert len(res) == 0  # pyright: ignore[reportUnknownArgumentType]

    results = exe.execute_flows_once()
    assert results["chunk_flow"] == 0
    assert results["metadata_flow"] == 1

    res = db.query("SELECT * FROM chunk WHERE meta IS NOT NONE", {}, dict)
    assert len(res) == 1  # pyright: ignore[reportUnknownArgumentType]

    results = exe.execute_flows_once()
    assert results["chunk_flow"] == 0
    assert results["metadata_flow"] == 0
