from collections import defaultdict, deque


VALID_RELATIONS = {
    "prerequisite",
    "related",
    "extends",
    "example_of",
}


def validate_relation(relation: str) -> str:
    relation = relation.strip().lower()

    if relation not in VALID_RELATIONS:
        raise ValueError(
            f"Invalid graph relation: {relation}. "
            f"Allowed: {sorted(VALID_RELATIONS)}"
        )

    return relation


def detect_cycles(
    node_ids: list[str],
    prerequisite_edges: list[tuple[str, str]],
) -> bool:
    """
    Detect cycles only in prerequisite relationships.

    Edge format:
        (prerequisite, dependent)
    """

    in_degree = {node_id: 0 for node_id in node_ids}
    graph = defaultdict(list)

    for prereq, dependent in prerequisite_edges:
        if prereq not in in_degree:
            in_degree[prereq] = 0

        if dependent not in in_degree:
            in_degree[dependent] = 0

        graph[prereq].append(dependent)
        in_degree[dependent] += 1

    queue = deque(
        node_id
        for node_id, degree in in_degree.items()
        if degree == 0
    )

    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1

        for neighbor in graph[node]:
            in_degree[neighbor] -= 1

            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return visited != len(in_degree)


def topological_order(
    node_ids: list[str],
    prerequisite_edges: list[tuple[str, str]],
) -> tuple[list[str], list[str]]:
    """
    Kahn's algorithm.

    Edge:
        (prerequisite, dependent)

    Returns:
        order, entry_points
    """

    in_degree = {node_id: 0 for node_id in node_ids}
    graph = defaultdict(list)

    for prereq, dependent in prerequisite_edges:
        if prereq not in in_degree:
            in_degree[prereq] = 0

        if dependent not in in_degree:
            in_degree[dependent] = 0

        graph[prereq].append(dependent)
        in_degree[dependent] += 1

    entry_points = [
        node_id
        for node_id in node_ids
        if in_degree[node_id] == 0
    ]

    queue = deque(entry_points)
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)

        for neighbor in graph[node]:
            in_degree[neighbor] -= 1

            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(in_degree):
        raise ValueError(
            "Knowledge graph contains a prerequisite cycle."
        )

    return order, entry_points


def topological_sort(
    concepts: list[dict],
    prerequisites: list[dict],
) -> tuple[list[str], list[dict]]:
    """Order extracted concepts and keep only safe prerequisite edges."""

    names_by_key = {}

    for concept in concepts:
        if not isinstance(concept, dict):
            continue

        name = concept.get("name")

        if not isinstance(name, str):
            continue

        name = name.strip()

        if name:
            names_by_key.setdefault(name.lower(), name)

    edges = []
    safe_edges = []
    seen_edges = set()

    for relation in prerequisites:
        if not isinstance(relation, dict):
            continue

        concept = relation.get("concept")
        prerequisite = relation.get("prerequisite")

        if not isinstance(concept, str) or not isinstance(prerequisite, str):
            continue

        concept = names_by_key.get(concept.strip().lower())
        prerequisite = names_by_key.get(prerequisite.strip().lower())

        if not concept or not prerequisite or concept == prerequisite:
            continue

        edge_key = (prerequisite.lower(), concept.lower())

        if edge_key in seen_edges:
            continue

        seen_edges.add(edge_key)
        edges.append(edge_key)
        safe_edges.append(
            {
                "concept": concept,
                "prerequisite": prerequisite,
            }
        )

    try:
        order, _ = topological_order(
            list(names_by_key.values()),
            edges,
        )
    except ValueError:
        return list(names_by_key.values()), []

    return order, safe_edges


def get_ready_nodes(
    node_ids: list[str],
    prerequisite_edges: list[tuple[str, str]],
    completed_node_ids: set[str],
) -> list[str]:
    """
    Return nodes whose prerequisites are all completed
    and which are not completed themselves.
    """

    prereqs_of = defaultdict(list)

    for prereq, dependent in prerequisite_edges:
        prereqs_of[dependent].append(prereq)

    return [
        node_id
        for node_id in node_ids
        if node_id not in completed_node_ids
        and all(
            prerequisite in completed_node_ids
            for prerequisite in prereqs_of.get(node_id, [])
        )
    ]


def build_adjacency(
    node_ids: list[str],
    edges: list[tuple[str, str, str]],
) -> dict[str, list[dict]]:
    """
    Build a generic adjacency representation.

    Edge:
        (from_node, to_node, relation)
    """

    graph = {node_id: [] for node_id in node_ids}

    for from_node, to_node, relation in edges:
        validate_relation(relation)

        graph.setdefault(from_node, [])
        graph[from_node].append(
            {
                "node_id": to_node,
                "relation": relation,
            }
        )

    return graph