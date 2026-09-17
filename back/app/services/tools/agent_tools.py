from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.concept import Concept, ConceptPrerequisite
from app.models.progress import StudentProgress
from app.services.retrieval import search_similar_chunks


def search_course_content(
    db: Session,
    course_id: str,
    query: str,
    node_id: str | None = None,
    top_k: int = 5,
) -> dict:
    """
    Search the uploaded course material using vector retrieval.
    The database remains the source of truth.
    """

    results = search_similar_chunks(
        course_id=course_id,
        query=query,
        node_id=node_id,
        top_k=top_k,
    )

    return {
        "tool": "search_course_content",
        "results": results,
    }


def get_student_progress(
    db: Session,
    user_id,
    course_id: str,
) -> dict:
    """
    Return the student's progress for concepts in this course.
    """

    rows = db.execute(
        select(StudentProgress, Concept)
        .join(
            Concept,
            StudentProgress.concept_id == Concept.id,
        )
        .where(
            StudentProgress.user_id == user_id,
            Concept.course_id == course_id,
        )
        .order_by(Concept.order_index)
    ).all()

    progress = []

    for student_progress, concept in rows:
        progress.append(
            {
                "concept_id": str(concept.id),
                "concept_name": concept.name,
                "status": student_progress.status,
                "completed_at": (
                    student_progress.completed_at.isoformat()
                    if student_progress.completed_at
                    else None
                ),
            }
        )

    return {
        "tool": "get_student_progress",
        "progress": progress,
    }


def get_graph_context(
    db: Session,
    course_id: str,
    concept_name: str | None = None,
) -> dict:
    """
    Return concept relationships and prerequisites
    from the course knowledge graph.
    """

    concepts_query = (
        select(Concept)
        .where(Concept.course_id == course_id)
        .order_by(Concept.order_index)
    )

    concepts = db.scalars(concepts_query).all()

    if concept_name:
        target = concept_name.strip().lower()

        concepts = [
            concept
            for concept in concepts
            if target in (concept.name or "").lower()
        ]

    concept_ids = {concept.id for concept in concepts}

    relations = []

    if concept_ids:
        relation_rows = db.scalars(
            select(ConceptPrerequisite).where(
                ConceptPrerequisite.concept_id.in_(concept_ids)
            )
        ).all()

        for relation in relation_rows:
            relations.append(
                {
                    "concept_id": str(relation.concept_id),
                    "prerequisite_concept_id": str(
                        relation.prerequisite_concept_id
                    ),
                }
            )

    return {
        "tool": "get_graph_context",
        "concepts": [
            {
                "id": str(concept.id),
                "name": concept.name,
                "description": concept.description or "",
                "order_index": concept.order_index,
            }
            for concept in concepts
        ],
        "relations": relations,
    }


def recommend_next_step(
    db: Session,
    user_id,
    course_id: str,
) -> dict:
    """
    Recommend the next concept based on the student's progress
    and prerequisite relationships.
    """

    concepts = db.scalars(
        select(Concept)
        .where(Concept.course_id == course_id)
        .order_by(Concept.order_index)
    ).all()

    progress_rows = db.scalars(
        select(StudentProgress).where(
            StudentProgress.user_id == user_id,
            StudentProgress.concept_id.in_(
                [concept.id for concept in concepts]
            ),
        )
    ).all()

    progress_by_concept = {
        row.concept_id: row.status
        for row in progress_rows
    }

    completed_ids = {
        concept_id
        for concept_id, status in progress_by_concept.items()
        if status == "completed"
    }

    for concept in concepts:
        status = progress_by_concept.get(
            concept.id,
            "not_started",
        )

        if status == "completed":
            continue

        prerequisites = db.scalars(
            select(ConceptPrerequisite).where(
                ConceptPrerequisite.concept_id == concept.id
            )
        ).all()

        prerequisite_ids = {
            relation.prerequisite_concept_id
            for relation in prerequisites
        }

        if prerequisite_ids.issubset(completed_ids):
            return {
                "tool": "recommend_next_step",
                "recommendation": {
                    "concept_id": str(concept.id),
                    "concept_name": concept.name,
                    "reason": (
                        "This concept is the next available concept "
                        "whose prerequisites are completed."
                    ),
                },
            }

    return {
        "tool": "recommend_next_step",
        "recommendation": None,
        "message": (
            "No next concept is currently available. "
            "The student may have completed all available concepts."
        ),
    }