"""add invoice number sequence

Revision ID: ADD_INVOICE_SEQUENCE
Revises: ADD_PROVIDER_EXTERNAL_ID_UNIQUE
"""

from typing import Sequence, Union

from alembic import op


revision: str = "ADD_INVOICE_SEQUENCE"
down_revision: Union[str, Sequence[str], None] = "ADD_PROVIDER_EXTERNAL_ID_UNIQUE"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE SEQUENCE IF NOT EXISTS invoice_number_seq
        START WITH 1001
        INCREMENT BY 1
        MINVALUE 1001
        """
    )

    op.alter_column(
        "invoices",
        "invoice_number",
        server_default="nextval('invoice_number_seq')",
    )


def downgrade() -> None:
    op.alter_column(
        "invoices",
        "invoice_number",
        server_default=None,
    )

    op.execute(
        "DROP SEQUENCE IF EXISTS invoice_number_seq"
    )