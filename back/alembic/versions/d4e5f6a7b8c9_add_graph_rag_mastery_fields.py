"""add graph rag mastery fields

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ai_interactions", sa.Column("node_id", sa.String(length=255), nullable=True))
    op.create_index("ix_ai_interactions_node_id", "ai_interactions", ["node_id"])

    op.create_table(
        "student_node_mastery",
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("node_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="not_started"),
        sa.Column("times_asked_about", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_interacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["node_id"], ["graph_nodes.node_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("student_id", "node_id"),
    )

    op.execute("UPDATE content_chunks SET embedding_model = 'intfloat/multilingual-e5-small' WHERE embedding_model = 'all-MiniLM-L6-v2'")


def downgrade() -> None:
    op.drop_table("student_node_mastery")
    op.drop_index("ix_ai_interactions_node_id", table_name="ai_interactions")
    op.drop_column("ai_interactions", "node_id")
