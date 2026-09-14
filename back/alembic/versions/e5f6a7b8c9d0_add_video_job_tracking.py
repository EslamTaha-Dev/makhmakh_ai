"""add video job tracking fields

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("processing_jobs", sa.Column("lesson_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_processing_jobs_lesson_id", "processing_jobs", "lessons", ["lesson_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_processing_jobs_lesson_id", "processing_jobs", ["lesson_id"])
    op.add_column("processing_jobs", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.add_column("processing_jobs", sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("processing_jobs", sa.Column("output_video_url", sa.Text(), nullable=True))
    op.add_column("processing_jobs", sa.Column("output_thumbnail_url", sa.Text(), nullable=True))
    op.add_column("processing_jobs", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_processing_jobs_content_hash", "processing_jobs", ["content_hash"])
    op.create_unique_constraint("uq_processing_job_material_hash", "processing_jobs", ["material_id", "content_hash"])
    op.create_unique_constraint("uq_processing_job_lesson_hash", "processing_jobs", ["lesson_id", "content_hash"])


def downgrade() -> None:
    op.drop_constraint("uq_processing_job_lesson_hash", "processing_jobs", type_="unique")
    op.drop_constraint("uq_processing_job_material_hash", "processing_jobs", type_="unique")
    op.drop_index("ix_processing_jobs_lesson_id", table_name="processing_jobs")
    op.drop_constraint("fk_processing_jobs_lesson_id", "processing_jobs", type_="foreignkey")
    op.drop_column("processing_jobs", "lesson_id")
    op.drop_index("ix_processing_jobs_content_hash", table_name="processing_jobs")
    for column in ("attempt_count", "output_thumbnail_url", "output_video_url", "progress_percent", "content_hash"):
        op.drop_column("processing_jobs", column)
