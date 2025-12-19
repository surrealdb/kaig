from __future__ import annotations

from dataclasses import dataclass

from surrealdb import RecordID

from kaig.db import utils as db_utils
from kaig.definitions import (
    RecordID as OwnRecordID,
)


@dataclass
class Child:
    id: OwnRecordID
    score: float


@dataclass
class Parent:
    id: OwnRecordID
    child: Child
    child_id: OwnRecordID
    children: list[Child]
    maybe: Child | None


def test_coerce_nested_dataclasses():
    raw = {
        "id": RecordID("parent", "1"),
        "child": {"id": RecordID("child", "1"), "score": 0.1},
        "child_id": RecordID("child", "1"),
        "children": [
            {"id": RecordID("child", "2"), "score": 0.2},
            {"id": RecordID("child", "3"), "score": 0.3},
        ],
        "maybe": None,
    }

    coerced = db_utils._coerce_value(raw, Parent)  # pyright: ignore[reportPrivateUsage, reportAny]

    assert isinstance(coerced, Parent)
    assert isinstance(coerced.child, Child)
    assert isinstance(coerced.child.id, RecordID)
    assert coerced.child.id.id == "1"  # pyright: ignore[reportAny]
    assert coerced.child.score == 0.1

    assert isinstance(coerced.children, list)
    assert [c.id.id for c in coerced.children] == ["2", "3"]  # pyright: ignore[reportAny]
    assert all(isinstance(c, Child) for c in coerced.children)
    assert coerced.maybe is None
