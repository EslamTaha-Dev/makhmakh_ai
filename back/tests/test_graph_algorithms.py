import pytest

from app.services.graph import get_ready_nodes, topological_order


def test_topological_order_returns_entry_points():
    order, entry_points = topological_order(
        ["a", "b", "c"],
        [("a", "b"), ("b", "c")],
    )

    assert order == ["a", "b", "c"]
    assert entry_points == ["a"]


def test_topological_order_rejects_cycles():
    with pytest.raises(ValueError, match="cycle"):
        topological_order(["a", "b"], [("a", "b"), ("b", "a")])


def test_ready_nodes_require_completed_prerequisites():
    assert get_ready_nodes(
        ["a", "b", "c"],
        [("a", "b"), ("b", "c")],
        {"a"},
    ) == ["b"]
