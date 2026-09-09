import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConceptResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    name: str
    description: str | None
    order_index: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConceptPrerequisiteResponse(BaseModel):
    id: uuid.UUID
    concept_id: uuid.UUID
    prerequisite_concept_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)