import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MaterialResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    uploaded_by: uuid.UUID
    file_name: str
    file_type: str
    storage_url: str | None
    processing_status: str
    error_message: str | None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)