import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.concept import Concept
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.lesson import LessonResponse
from app.services.queue import video_queue


router = APIRouter(
    prefix="/lessons",
    tags=["Lessons"],
)


CONTENT_MANAGEMENT_ROLES = (
    "instructor",
    "content_creator",
    "admin",
    "super_admin",
)


@router.post(
    "/concepts/{concept_id}",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson(
    concept_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*CONTENT_MANAGEMENT_ROLES)
    ),
):
    concept = db.scalar(
        select(Concept).where(
            Concept.id == concept_id
        )
    )

    if concept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Concept not found",
        )

    lesson = Lesson(
        concept_id=concept.id,
        status="pending",
    )

    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    try:
        video_queue.enqueue(
            "app.services.lesson_job.generate_lesson_job",
            str(lesson.id),
        )
    except Exception as exc:
        lesson.status = "failed"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue lesson generation",
        ) from exc

    return lesson


@router.get(
    "/{lesson_id}",
    response_model=LessonResponse,
)
def get_lesson(
    lesson_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = db.scalar(
        select(Lesson).where(
            Lesson.id == lesson_id
        )
    )

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    return lesson