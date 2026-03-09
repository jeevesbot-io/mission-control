"""add_logging_columns_to_agent_runs

Revision ID: 731ce699267c
Revises: fac85843c830
Create Date: 2026-03-09 17:07:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "731ce699267c"
down_revision: Union[str, Sequence[str], None] = "fac85843c830"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add logging columns to agent_runs."""
    op.add_column("agent_runs", sa.Column("prompt_preview", sa.String(length=500), nullable=True))
    op.add_column("agent_runs", sa.Column("channel", sa.String(length=100), nullable=True))
    op.add_column("agent_runs", sa.Column("session_key", sa.String(length=200), nullable=True))
    op.add_column(
        "agent_runs", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("agent_runs", sa.Column("outcome", sa.String(length=20), nullable=True))
    # Index on outcome for filtering
    op.create_index("ix_agent_runs_outcome", "agent_runs", ["outcome"], unique=False)
    op.create_index("ix_agent_runs_channel", "agent_runs", ["channel"], unique=False)


def downgrade() -> None:
    """Remove logging columns from agent_runs."""
    op.drop_index("ix_agent_runs_channel", table_name="agent_runs")
    op.drop_index("ix_agent_runs_outcome", table_name="agent_runs")
    op.drop_column("agent_runs", "outcome")
    op.drop_column("agent_runs", "completed_at")
    op.drop_column("agent_runs", "session_key")
    op.drop_column("agent_runs", "channel")
    op.drop_column("agent_runs", "prompt_preview")
