import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    price: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)


class CourseResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    price: Decimal
    created_by: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)