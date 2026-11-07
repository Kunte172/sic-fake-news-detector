"""Add source URL to analyses.

Revision ID: c9e1f4a7b2d8
Revises: a1b2c3d4e5f6
"""

from alembic import op
import sqlalchemy as sa

revision = "c9e1f4a7b2d8"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("source_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "source_url")
