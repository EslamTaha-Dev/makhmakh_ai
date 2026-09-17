"""add course price

Revision ID: 2b7be2606975
Revises: e9e301c92415
Create Date: 2026-09-12 22:09:07.682469

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2b7be2606975"
down_revision: Union[str, Sequence[str], None] = "e9e301c92415"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "courses",
        sa.Column(
            "price",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
    )

    op.alter_column(
        "courses",
        "price",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("courses", "price")