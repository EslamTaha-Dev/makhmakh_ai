"""add student dashboard schema

Revision ID: a1b2c3d4e5f6
Revises: 47881f3a7239
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "47881f3a7239"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE courses SET updated_at = created_at WHERE updated_at IS NULL")
    op.alter_column("courses", "updated_at", nullable=False)

    op.create_table(
        "course_modules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_course_modules_course_id", "course_modules", ["course_id"])

    op.add_column("lessons", sa.Column("module_id", sa.UUID(), nullable=True))
    op.add_column("lessons", sa.Column("course_id", sa.UUID(), nullable=True))
    op.add_column("lessons", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("lessons", sa.Column("order_index", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("lessons", sa.Column("estimated_minutes", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_lessons_module_id", "lessons", "course_modules", ["module_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_lessons_course_id", "lessons", "courses", ["course_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_lessons_module_id", "lessons", ["module_id"])
    op.create_index("ix_lessons_course_id", "lessons", ["course_id"])

    op.create_table(
        "enrollments",
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="free"),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("student_id", "course_id"),
    )
    op.create_index("ix_enrollments_course_id", "enrollments", ["course_id"])

    op.create_table(
        "student_lesson_progress",
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("lesson_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="not_started"),
        sa.Column("video_watched_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("student_id", "lesson_id"),
    )

    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_conversations_student_id", "ai_conversations", ["student_id"])
    op.create_index("ix_ai_conversations_course_id", "ai_conversations", ["course_id"])

    op.create_table(
        "ai_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("interaction_id", sa.UUID(), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interaction_id"], ["ai_interactions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_messages_conversation_id", "ai_messages", ["conversation_id"])

    op.add_column("ai_interactions", sa.Column("conversation_id", sa.UUID(), nullable=True))
    op.add_column("ai_interactions", sa.Column("request_id", sa.UUID(), nullable=True))
    op.add_column("ai_interactions", sa.Column("trace_id", sa.UUID(), nullable=True))
    op.add_column("ai_interactions", sa.Column("model_version", sa.String(length=100), nullable=True))
    op.add_column("ai_interactions", sa.Column("system_prompt_version", sa.String(length=100), nullable=True))
    op.add_column("ai_interactions", sa.Column("rag_pipeline_version", sa.String(length=100), nullable=True))
    op.add_column("ai_interactions", sa.Column("agent_version", sa.String(length=100), nullable=True))
    op.add_column("ai_interactions", sa.Column("interaction_status", sa.String(length=20), nullable=False, server_default="success"))
    op.add_column("ai_interactions", sa.Column("error_code", sa.String(length=100), nullable=True))
    op.add_column("ai_interactions", sa.Column("estimated_cost_usd", sa.Numeric(10, 6), nullable=True))
    op.add_column("ai_interactions", sa.Column("actual_cost_usd", sa.Numeric(10, 6), nullable=True))
    op.create_foreign_key("fk_ai_interactions_conversation_id", "ai_interactions", "ai_conversations", ["conversation_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_ai_interactions_conversation_id", "ai_interactions", ["conversation_id"])
    op.create_index("ix_ai_interactions_request_id", "ai_interactions", ["request_id"])

    op.create_table(
        "video_assets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("processing_job_id", sa.UUID(), nullable=False),
        sa.Column("asset_type", sa.String(length=30), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["processing_job_id"], ["processing_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_video_assets_processing_job_id", "video_assets", ["processing_job_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.add_column("content_chunks", sa.Column("embedding_model", sa.String(length=100), nullable=True))
    op.add_column("content_chunks", sa.Column("embedding_dimension", sa.Integer(), nullable=True))
    op.execute("UPDATE content_chunks SET embedding_model = 'all-MiniLM-L6-v2' WHERE embedding_model IS NULL")
    op.execute("UPDATE content_chunks SET embedding_dimension = 384 WHERE embedding_dimension IS NULL")
    op.alter_column("content_chunks", "embedding_model", nullable=False)
    op.alter_column("content_chunks", "embedding_dimension", nullable=False)
    op.create_index("ix_content_chunks_embedding_model", "content_chunks", ["embedding_model"])


def downgrade() -> None:
    op.drop_index("ix_content_chunks_embedding_model", table_name="content_chunks")
    op.drop_column("content_chunks", "embedding_dimension")
    op.drop_column("content_chunks", "embedding_model")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_video_assets_processing_job_id", table_name="video_assets")
    op.drop_table("video_assets")
    op.drop_index("ix_ai_interactions_request_id", table_name="ai_interactions")
    op.drop_index("ix_ai_interactions_conversation_id", table_name="ai_interactions")
    op.drop_constraint("fk_ai_interactions_conversation_id", "ai_interactions", type_="foreignkey")
    for column in ("actual_cost_usd", "estimated_cost_usd", "error_code", "interaction_status", "agent_version", "rag_pipeline_version", "system_prompt_version", "model_version", "trace_id", "request_id", "conversation_id"):
        op.drop_column("ai_interactions", column)
    op.drop_index("ix_ai_messages_conversation_id", table_name="ai_messages")
    op.drop_table("ai_messages")
    op.drop_index("ix_ai_conversations_course_id", table_name="ai_conversations")
    op.drop_index("ix_ai_conversations_student_id", table_name="ai_conversations")
    op.drop_table("ai_conversations")
    op.drop_table("student_lesson_progress")
    op.drop_index("ix_enrollments_course_id", table_name="enrollments")
    op.drop_table("enrollments")
    op.drop_index("ix_lessons_course_id", table_name="lessons")
    op.drop_index("ix_lessons_module_id", table_name="lessons")
    op.drop_constraint("fk_lessons_course_id", "lessons", type_="foreignkey")
    op.drop_constraint("fk_lessons_module_id", "lessons", type_="foreignkey")
    for column in ("estimated_minutes", "order_index", "title", "course_id", "module_id"):
        op.drop_column("lessons", column)
    op.drop_index("ix_course_modules_course_id", table_name="course_modules")
    op.drop_table("course_modules")
    op.drop_column("courses", "updated_at")
