"""Add claimed_by and claimed_at columns to mc_tasks.

Revision ID: d6f3a4b5c7e8
Revises: c5e2f3a4b6d7
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa

revision = "d6f3a4b5c7e8"
down_revision = "c5e2f3a4b6d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("mc_tasks", sa.Column("claimed_by", sa.Text(), nullable=True))
    op.add_column(
        "mc_tasks",
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "idx_mc_tasks_claimed",
        "mc_tasks",
        ["claimed_by"],
        postgresql_where=sa.text("claimed_by IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_mc_tasks_claimed", "mc_tasks")
    op.drop_column("mc_tasks", "claimed_at")
    op.drop_column("mc_tasks", "claimed_by")
