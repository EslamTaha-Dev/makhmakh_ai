import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    tools_used: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    retrieved_chunks: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sources: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    feedback: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    node_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    trace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    system_prompt_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rag_pipeline_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    agent_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    interaction_status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    actual_cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="ai_interactions",
    )

    message = relationship("AIMessage", back_populates="interaction", uselist=False)