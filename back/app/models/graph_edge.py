import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


GRAPH_RELATIONS = {
    "prerequisite",
    "related",
    "extends",
    "example_of",
}


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    from_node: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("graph_nodes.node_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    to_node: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("graph_nodes.node_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    relation: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    from_node_relation = relationship(
        "GraphNode",
        foreign_keys=[from_node],
        back_populates="outgoing_edges",
    )

    to_node_relation = relationship(
        "GraphNode",
        foreign_keys=[to_node],
        back_populates="incoming_edges",
    )