import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.concept import Concept, ConceptPrerequisite
from app.models.course import Course
from app.models.user import User


router = APIRouter(
    prefix="/courses",
    tags=["Learning Map"],
)


@router.get("/{course_id}/map")
def get_course_map(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.scalar(
        select(Course).where(
            Course.id == course_id
        )
    )

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    concepts = db.scalars(
        select(Concept)
        .where(
            Concept.course_id == course_id
        )
        .order_by(Concept.order_index)
    ).all()

    concept_ids = [concept.id for concept in concepts]

    prerequisites = []

    if concept_ids:
        prerequisites = db.scalars(
            select(ConceptPrerequisite).where(
                ConceptPrerequisite.concept_id.in_(
                    concept_ids
                )
            )
        ).all()

    prerequisite_map = {}

    for item in prerequisites:
        prerequisite_map.setdefault(
            str(item.concept_id),
            [],
        ).append(
            str(item.prerequisite_concept_id)
        )

    return {
        "course_id": course.id,
        "course_name": course.name,
        "concepts": [
            {
                "id": str(concept.id),
                "name": concept.name,
                "description": concept.description,
                "order_index": concept.order_index,
                "prerequisites": prerequisite_map.get(
                    str(concept.id),
                    [],
                ),
            }
            for concept in concepts
        ],
    }