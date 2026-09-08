from collections import defaultdict, deque


def build_graph(
    concepts: list[dict],
    prerequisites: list[dict],
):
    names = {
        concept["name"].lower(): concept["name"]
        for concept in concepts
    }

    graph = defaultdict(set)
    indegree = {
        concept["name"]: 0
        for concept in concepts
    }

    valid_edges = []

    for relation in prerequisites:
        concept_name = names.get(
            relation["concept"].lower()
        )

        prerequisite_name = names.get(
            relation["prerequisite"].lower()
        )

        if not concept_name or not prerequisite_name:
            continue

        if concept_name == prerequisite_name:
            continue

        if concept_name in graph[prerequisite_name]:
            continue

        graph[prerequisite_name].add(
            concept_name
        )

        indegree[concept_name] += 1

        valid_edges.append(
            {
                "concept": concept_name,
                "prerequisite": prerequisite_name,
            }
        )

    return graph, indegree, valid_edges


def topological_sort(
    concepts: list[dict],
    prerequisites: list[dict],
):
    graph, indegree, edges = build_graph(
        concepts,
        prerequisites,
    )

    queue = deque(
        name
        for name, degree in indegree.items()
        if degree == 0
    )

    ordered = []

    while queue:
        current = queue.popleft()

        ordered.append(current)

        for neighbor in graph[current]:
            indegree[neighbor] -= 1

            if indegree[neighbor] == 0:
                queue.append(neighbor)

    has_cycle = len(ordered) != len(indegree)

    if not has_cycle:
        return ordered, edges

    # Break cycles conservatively.
    safe_edges = []
    current_edges = list(edges)

    while current_edges:
        graph, indegree, _ = build_graph(
            concepts,
            current_edges,
        )

        queue = deque(
            name
            for name, degree in indegree.items()
            if degree == 0
        )

        ordered = []

        while queue:
            current = queue.popleft()
            ordered.append(current)

            for neighbor in graph[current]:
                indegree[neighbor] -= 1

                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered) == len(indegree):
            safe_edges = current_edges
            break

        # Remove one edge from the remaining cycle.
        current_edges.pop()

    return ordered, safe_edges