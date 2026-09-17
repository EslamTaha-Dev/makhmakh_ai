"""scope payment event uniqueness by provider

Revision ID: 778f2b88aef7
Revises: e13c98b708fa
Create Date: 2026-09-13 01:39:20.435468
"""

from typing import Sequence, Union

from alembic import op


revision: str = "778f2b88aef7"
down_revision: Union[str, Sequence[str], None] = "e13c98b708fa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove the old globally-unique event_id index.
    op.drop_index(
        "ix_payment_events_event_id",
        table_name="payment_events",
    )

    # Create a normal index for event_id lookups.
    op.create_index(
        "ix_payment_events_event_id",
        "payment_events",
        ["event_id"],
        unique=False,
    )

    # Make event_id unique only within each payment provider.
    op.create_index(
        "uq_payment_event_provider_event_id",
        "payment_events",
        ["provider", "event_id"],
        unique=True,
    )


def downgrade() -> None:
    # Remove provider-scoped uniqueness.
    op.drop_index(
        "uq_payment_event_provider_event_id",
        table_name="payment_events",
    )

    # Remove the normal event_id index.
    op.drop_index(
        "ix_payment_events_event_id",
        table_name="payment_events",
    )

    # Restore the original globally-unique event_id index.
    op.create_index(
        "ix_payment_events_event_id",
        "payment_events",
        ["event_id"],
        unique=True,
    )