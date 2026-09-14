"""add identity security fields

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("status", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE users SET status = 'active' WHERE status IS NULL")
    op.execute("UPDATE users SET updated_at = created_at WHERE updated_at IS NULL")
    op.alter_column("users", "status", nullable=False)
    op.alter_column("users", "updated_at", nullable=False)
    op.create_index("ix_users_status", "users", ["status"])

    op.add_column("refresh_tokens", sa.Column("family_id", sa.UUID(), nullable=True))
    op.add_column("refresh_tokens", sa.Column("device_label", sa.String(length=255), nullable=True))
    op.add_column("refresh_tokens", sa.Column("ip_address", sa.String(length=45), nullable=True))
    op.add_column("refresh_tokens", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("refresh_tokens", sa.Column("revoked_reason", sa.String(length=50), nullable=True))
    op.execute("UPDATE refresh_tokens SET family_id = id WHERE family_id IS NULL")
    op.alter_column("refresh_tokens", "family_id", nullable=False)
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])

    op.create_table(
        "oauth_accounts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("provider_account_id", sa.String(length=255), nullable=False),
        sa.Column("provider_email", sa.String(length=255), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_account_id", name="uq_oauth_provider_account"),
    )
    op.create_index("ix_oauth_accounts_user_id", "oauth_accounts", ["user_id"])

    for table in ("password_reset_tokens", "email_verification_tokens"):
        op.create_table(
            table,
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("token_hash", sa.String(length=255), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash"),
        )
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])

    op.create_table(
        "mfa_secrets",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("totp_secret", sa.String(length=512), nullable=False),
        sa.Column("enabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "mfa_recovery_codes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mfa_recovery_codes_user_id", "mfa_recovery_codes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_mfa_recovery_codes_user_id", table_name="mfa_recovery_codes")
    op.drop_table("mfa_recovery_codes")
    op.drop_table("mfa_secrets")
    for table in ("email_verification_tokens", "password_reset_tokens"):
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_table(table)
    op.drop_index("ix_oauth_accounts_user_id", table_name="oauth_accounts")
    op.drop_table("oauth_accounts")
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    for column in ("revoked_reason", "revoked_at", "ip_address", "device_label", "family_id"):
        op.drop_column("refresh_tokens", column)
    op.drop_index("ix_users_status", table_name="users")
    for column in ("updated_at", "status", "email_verified_at"):
        op.drop_column("users", column)
