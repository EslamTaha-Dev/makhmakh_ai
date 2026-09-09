import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProgressResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    concept_id: uuid.UUID
    status: str
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)