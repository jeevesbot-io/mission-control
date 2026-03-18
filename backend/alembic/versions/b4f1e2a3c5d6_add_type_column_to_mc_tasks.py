"""Add type column to mc_tasks.

Revision ID: b4f1e2a3c5d6
Revises: 23fc0ed9f1c9
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa

revision = "b4f1e2a3c5d6"
down_revision = "23fc0ed9f1c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "mc_tasks",
        sa.Column(
            "type",
            sa.Text(),
            nullable=False,
            server_default="feature",
        ),
    )
    op.create_check_constraint(
        "mc_tasks_type_check",
        "mc_tasks",
        "type IN ('feature', 'bug', 'debt', 'investigation', 'chore')",
    )


def downgrade() -> None:
    op.drop_constraint("mc_tasks_type_check", "mc_tasks")
    op.drop_column("mc_tasks", "type")
