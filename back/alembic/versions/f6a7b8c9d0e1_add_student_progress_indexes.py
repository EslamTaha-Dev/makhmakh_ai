"""add student progress indexes

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""
from typing import Sequence, Union

from alembic import op


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_student_progress_user_id", "student_progress", ["user_id"])
    op.create_index("ix_student_progress_concept_id", "student_progress", ["concept_id"])


def downgrade() -> None:
    op.drop_index("ix_student_progress_concept_id", table_name="student_progress")
    op.drop_index("ix_student_progress_user_id", table_name="student_progress")
