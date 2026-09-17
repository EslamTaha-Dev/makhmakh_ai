import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LessonResponse(BaseModel):
    id: uuid.UUID
    concept_id: uuid.UUID
    script_text: str | None
    audio_url: str | None
    video_url: str | None
    duration_seconds: float | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)