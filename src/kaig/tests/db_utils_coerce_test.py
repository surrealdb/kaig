from __future__ import annotations

from dataclasses import dataclass

from kaig.db import utils as db_utils


@dataclass
class Child:
    id: str
    score: float


@dataclass
class Parent:
    child: Child
    children: list[Child]
    maybe: Child | None


def test_coerce_nested_dataclasses():
    raw = {
        "child": {"id": "c1", "score": 0.1},
        "children": [{"id": "c2", "score": 0.2}, {"id": "c3", "score": 0.3}],
        "maybe": None,
    }

    coerced = db_utils._coerce_value(raw, Parent)  # pyright: ignore[reportPrivateUsage, reportAny]

    assert isinstance(coerced, Parent)
    assert isinstance(coerced.child, Child)
    assert coerced.child.id == "c1"
    assert coerced.child.score == 0.1

    assert isinstance(coerced.children, list)
    assert [c.id for c in coerced.children] == ["c2", "c3"]
    assert all(isinstance(c, Child) for c in coerced.children)
    assert coerced.maybe is None
