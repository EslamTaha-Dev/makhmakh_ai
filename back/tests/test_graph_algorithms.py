import pytest

from app.services.graph import get_ready_nodes, topological_order
from app.services.graph_builder import make_node_id


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


def test_graph_node_ids_preserve_arabic_concept_names():
    course_id = "640dc6f2-9f62-40ba-bc3f-4e0c8bdc50fc"

    first = make_node_id(course_id, "نظام القلعة")
    second = make_node_id(course_id, "شركة الوثاق")

    assert first == f"{course_id}_نظام_القلعة"
    assert second == f"{course_id}_شركة_الوثاق"
    assert first != second
