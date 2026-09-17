from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.course import Course
from app.models.user import User
from app.services.evaluation import evaluate_questions


router = APIRouter(
    prefix="/courses",
    tags=["evaluation"],
)


class EvaluationRequest(BaseModel):
    questions: list[str] = Field(
        min_length=1,
        max_length=50,
    )


@router.post("/{course_id}/evaluation")
def evaluate_course(
    course_id: UUID,
    data: EvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.scalar(
        select(Course).where(Course.id == course_id)
    )

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    questions = [
        question.strip()
        for question in data.questions
        if isinstance(question, str) and question.strip()
    ]

    if not questions:
        raise HTTPException(
            status_code=400,
            detail="At least one valid question is required",
        )

    return evaluate_questions(
        course_id=str(course_id),
        questions=questions,
    )