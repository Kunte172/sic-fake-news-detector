"""Add per-user analysis history and feedback.

Revision ID: 6b74a2d90f31
Revises: 0f4b5cae6a63
"""

from alembic import op
import sqlalchemy as sa

revision = "6b74a2d90f31"
down_revision = "0f4b5cae6a63"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("input_type", sa.String(length=16), nullable=False),
        sa.Column("content_preview", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analyses_user_id", "analyses", ["user_id"])
    op.create_index("ix_analyses_created_at", "analyses", ["created_at"])
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("analyses.id"), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("agree", sa.Boolean(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_feedbacks_created_at", "feedbacks", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_feedbacks_created_at", table_name="feedbacks")
    op.drop_table("feedbacks")
    op.drop_index("ix_analyses_created_at", table_name="analyses")
    op.drop_index("ix_analyses_user_id", table_name="analyses")
    op.drop_table("analyses")
