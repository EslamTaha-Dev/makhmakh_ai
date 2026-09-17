"""add provider external id uniqueness

Revision ID: ADD_PROVIDER_EXTERNAL_ID_UNIQUE
Revises: 778f2b88aef7
"""

from typing import Sequence, Union

from alembic import op


revision: str = "ADD_PROVIDER_EXTERNAL_ID_UNIQUE"
down_revision: Union[str, Sequence[str], None] = "778f2b88aef7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_payment_provider_external_id",
        "payments",
        ["provider", "external_id"],
        unique=True,
        postgresql_where=(
            "external_id IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_payment_provider_external_id",
        table_name="payments",
    )