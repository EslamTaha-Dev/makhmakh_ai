import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StudentNodeMastery(Base):
    __tablename__ = "student_node_mastery"

    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    node_id: Mapped[str] = mapped_column(String(255), ForeignKey("graph_nodes.node_id", ondelete="CASCADE"), primary_key=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="not_started")
    times_asked_about: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_interacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student = relationship("User")
    node = relationship("GraphNode")
