import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_student
from app.db.session import get_db
from app.models.concept import Concept
from app.models.progress import StudentProgress
from app.models.user import User
from app.schemas.progress import ProgressResponse
from app.services.progress_service import refresh_user_progress


router = APIRouter(
    tags=["Progress"],
)


@router.post(
    "/concepts/{concept_id}/progress/complete",
    response_model=ProgressResponse,
)
def complete_concept(
    concept_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
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

    progress = db.scalar(
        select(StudentProgress).where(
            StudentProgress.user_id == current_user.id,
            StudentProgress.concept_id == concept_id,
        )
    )

    now = datetime.now(timezone.utc)

    if progress is None:
        progress = StudentProgress(
            user_id=current_user.id,
            concept_id=concept_id,
            status="completed",
            completed_at=now,
        )

        db.add(progress)

    else:
        progress.status = "completed"
        progress.completed_at = now

    refresh_user_progress(
        db=db,
        user_id=current_user.id,
        course_id=concept.course_id,
    )

    db.commit()
    db.refresh(progress)

    return progress


@router.get(
    "/users/me/progress",
    response_model=list[ProgressResponse],
)
def get_my_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    progress = db.scalars(
        select(StudentProgress)
        .where(
            StudentProgress.user_id == current_user.id
        )
        .order_by(StudentProgress.concept_id)
    ).all()

    return progress