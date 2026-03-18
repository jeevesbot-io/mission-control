"""Add proof JSONB column to mc_tasks.

Revision ID: c5e2f3a4b6d7
Revises: b4f1e2a3c5d6
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "c5e2f3a4b6d7"
down_revision = "b4f1e2a3c5d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "mc_tasks",
        sa.Column("proof", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("mc_tasks", "proof")
