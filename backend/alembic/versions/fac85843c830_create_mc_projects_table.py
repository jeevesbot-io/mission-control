"""create mc_projects table

Revision ID: fac85843c830
Revises: 2788da5d5c5c
Create Date: 2026-03-05 22:35:14.088846

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "fac85843c830"
down_revision: Union[str, Sequence[str], None] = "2788da5d5c5c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create trigger function if it doesn't exist
    op.execute("""
CREATE OR REPLACE FUNCTION mc_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")

    op.execute("""
CREATE TABLE IF NOT EXISTS mc_projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '',
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'archived')),
    "order" INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
""")

    op.execute("""
CREATE TRIGGER mc_projects_updated
    BEFORE UPDATE ON mc_projects
    FOR EACH ROW EXECUTE FUNCTION mc_update_timestamp();
""")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS mc_projects")
