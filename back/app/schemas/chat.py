import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=5000,
    )

    session_id: uuid.UUID | None = None
    node_id: str | None = Field(default=None, max_length=255)


class ChatSource(BaseModel):
    chunk_id: uuid.UUID | None = None
    material_id: uuid.UUID
    file_name: str
    text: str
    distance: float


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    sources: list[ChatSource] = Field(
        default_factory=list
    )


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    sources: list | None
    created_at: datetime