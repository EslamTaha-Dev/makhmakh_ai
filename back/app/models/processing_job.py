import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    __table_args__ = (
        UniqueConstraint("material_id", "content_hash", name="uq_processing_job_material_hash"),
        UniqueConstraint("lesson_id", "content_hash", name="uq_processing_job_lesson_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    material_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=True,
    )

    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    material = relationship(
        "Material",
        back_populates="processing_jobs",
    )

    video_assets = relationship(
        "VideoAsset",
        back_populates="processing_job",
        cascade="all, delete-orphan",
    )

    lesson = relationship("Lesson", back_populates="processing_jobs")