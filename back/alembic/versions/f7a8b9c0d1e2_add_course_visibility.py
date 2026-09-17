"""add course visibility

Courses are either published into the shared catalog (``public``) or kept as a
student's private study space (``private``), which is where a student uploads their
own lecture material.

Revision ID: f7a8b9c0d1e2
Revises: 906939186f76
Create Date: 2026-09-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = "906939186f76"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "courses",
        sa.Column(
            "visibility",
            sa.String(length=20),
            nullable=False,
            server_default="public",
        ),
    )

    op.create_index(
        "ix_courses_visibility",
        "courses",
        ["visibility"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_courses_visibility",
        table_name="courses",
    )

    op.drop_column("courses", "visibility")
