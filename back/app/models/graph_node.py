import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    node_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    module: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    difficulty: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="beginner",
    )

    estimated_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
    )

    source_pages: Mapped[list[int] | None] = mapped_column(
        ARRAY(Integer),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    outgoing_edges = relationship(
        "GraphEdge",
        foreign_keys="GraphEdge.from_node",
        back_populates="from_node_relation",
        cascade="all, delete-orphan",
    )

    incoming_edges = relationship(
        "GraphEdge",
        foreign_keys="GraphEdge.to_node",
        back_populates="to_node_relation",
        cascade="all, delete-orphan",
    )