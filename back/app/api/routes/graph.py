import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.graph_edge import GraphEdge
from app.models.graph_node import GraphNode
from app.services.graph import (
    get_ready_nodes,
    topological_order,
)
from app.services.graph_builder import build_course_graph
from app.models.progress import StudentProgress
from app.models.concept import Concept


router = APIRouter(
    prefix="/courses",
    tags=["Knowledge Graph"],
)


@router.post("/{course_id}/graph/build")
def build_graph(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return build_course_graph(
        db=db,
        course_id=course_id,
    )


@router.get("/{course_id}/graph")
def get_graph(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    nodes = db.scalars(
        select(GraphNode)
        .where(GraphNode.course_id == course_id)
        .order_by(GraphNode.title)
    ).all()

    edges = db.scalars(
        select(GraphEdge)
        .where(GraphEdge.course_id == course_id)
    ).all()

    return {
        "nodes": [
            {
                "node_id": node.node_id,
                "course_id": str(node.course_id),
                "module": node.module,
                "title": node.title,
                "summary": node.summary,
                "difficulty": node.difficulty,
                "estimated_minutes": node.estimated_minutes,
                "source_pages": node.source_pages,
            }
            for node in nodes
        ],
        "edges": [
            {
                "from_node": edge.from_node,
                "to_node": edge.to_node,
                "relation": edge.relation,
            }
            for edge in edges
        ],
    }


@router.get("/{course_id}/graph/order")
def get_graph_order(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    nodes = db.scalars(
        select(GraphNode)
        .where(GraphNode.course_id == course_id)
    ).all()

    edges = db.scalars(
        select(GraphEdge)
        .where(
            GraphEdge.course_id == course_id,
            GraphEdge.relation == "prerequisite",
        )
    ).all()

    node_ids = [node.node_id for node in nodes]

    prerequisite_edges = [
        (edge.from_node, edge.to_node)
        for edge in edges
    ]

    try:
        order, entry_points = topological_order(
            node_ids=node_ids,
            prerequisite_edges=prerequisite_edges,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "order": order,
        "entry_points": entry_points,
    }


@router.get("/{course_id}/graph/ready")
def get_graph_ready_nodes(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    nodes = db.scalars(
        select(GraphNode)
        .where(GraphNode.course_id == course_id)
    ).all()

    edges = db.scalars(
        select(GraphEdge)
        .where(
            GraphEdge.course_id == course_id,
            GraphEdge.relation == "prerequisite",
        )
    ).all()

    completed_concepts = db.scalars(
        select(StudentProgress)
        .join(
            Concept,
            Concept.id == StudentProgress.concept_id,
        )
        .where(
            StudentProgress.user_id == current_user.id,
            StudentProgress.status == "completed",
            Concept.course_id == course_id,
        )
    ).all()

    completed_node_ids = set()

    concept_by_id = {
        str(concept.id): concept
        for concept in db.scalars(
            select(Concept)
            .where(Concept.course_id == course_id)
        ).all()
    }

    node_by_title = {
        node.title: node.node_id
        for node in nodes
    }

    for progress in completed_concepts:
        concept = concept_by_id.get(
            str(progress.concept_id)
        )

        if concept:
            node_id = node_by_title.get(concept.name)

            if node_id:
                completed_node_ids.add(node_id)

    node_ids = [node.node_id for node in nodes]

    prerequisite_edges = [
        (edge.from_node, edge.to_node)
        for edge in edges
    ]

    ready = get_ready_nodes(
        node_ids=node_ids,
        prerequisite_edges=prerequisite_edges,
        completed_node_ids=completed_node_ids,
    )

    return {
        "ready_nodes": ready,
        "completed_nodes": list(completed_node_ids),
    }