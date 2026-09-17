import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.concept import Concept
from app.models.user import User
from app.schemas.concept import ConceptResponse


router = APIRouter(
    prefix="/concepts",
    tags=["Concepts"],
)


@router.get(
    "/{concept_id}",
    response_model=ConceptResponse,
)
def get_concept(
    concept_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    return concept