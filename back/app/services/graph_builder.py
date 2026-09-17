import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.concept import Concept, ConceptPrerequisite
from app.models.graph_edge import GraphEdge
from app.models.graph_node import GraphNode
from app.services.graph import validate_relation
from app.services.graph import topological_order


def make_node_id(course_id: str, concept_name: str) -> str:
    slug = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        concept_name.strip().lower(),
    ).strip("_")

    return f"{course_id}_{slug}"


def build_course_graph(
    db: Session,
    course_id,
) -> dict:

    concepts = db.scalars(
        select(Concept)
        .where(Concept.course_id == course_id)
        .order_by(Concept.order_index)
    ).all()

    if not concepts:
        return {
            "nodes_created": 0,
            "edges_created": 0,
        }

    concept_to_node = {}

    nodes_created = 0

    for concept in concepts:
        node_id = make_node_id(
            str(course_id),
            concept.name,
        )

        existing = db.scalar(
            select(GraphNode).where(
                GraphNode.node_id == node_id
            )
        )

        if existing:
            node = existing

        else:
            node = GraphNode(
                node_id=node_id,
                course_id=course_id,
                module="Course",
                title=concept.name,
                summary=concept.description or "",
                difficulty="beginner",
                estimated_minutes=10,
                source_pages=None,
            )

            db.add(node)
            nodes_created += 1

        concept_to_node[str(concept.id)] = node_id

    db.flush()

    prerequisites = db.scalars(
        select(ConceptPrerequisite)
        .join(
            Concept,
            Concept.id == ConceptPrerequisite.concept_id,
        )
        .where(
            Concept.course_id == course_id
        )
    ).all()

    edges_created = 0

    prerequisite_pairs = []

    for prerequisite in prerequisites:

        dependent_node = concept_to_node.get(
            str(prerequisite.concept_id)
        )

        prerequisite_node = concept_to_node.get(
            str(prerequisite.prerequisite_concept_id)
        )

        if not dependent_node or not prerequisite_node:
            continue

        prerequisite_pairs.append(
            (prerequisite_node, dependent_node)
        )

        existing_edge = db.scalar(
            select(GraphEdge).where(
                GraphEdge.from_node == prerequisite_node,
                GraphEdge.to_node == dependent_node,
                GraphEdge.relation == "prerequisite",
            )
        )

        if existing_edge:
            continue

        edge = GraphEdge(
            course_id=course_id,
            from_node=prerequisite_node,
            to_node=dependent_node,
            relation=validate_relation("prerequisite"),
        )

        db.add(edge)
        edges_created += 1

    try:
        topological_order(
            node_ids=list(concept_to_node.values()),
            prerequisite_edges=prerequisite_pairs,
        )
    except ValueError:
        db.rollback()
        raise ValueError(
            "Knowledge graph contains a prerequisite cycle."
        )

    db.commit()

    return {
        "nodes_created": nodes_created,
        "edges_created": edges_created,
    }