"""alter mc_tasks add warroom columns

Revision ID: ddde276426d8
Revises: 942b3f740909
Create Date: 2026-03-05 22:34:40.756361

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "ddde276426d8"
down_revision: Union[str, Sequence[str], None] = "942b3f740909"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS slug TEXT")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS project TEXT")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}'")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS skill TEXT")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS schedule TEXT")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS references_ JSONB DEFAULT '[]'")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS blocked_by TEXT[] DEFAULT '{}'")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS blocks TEXT[] DEFAULT '{}'")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS result TEXT")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS error TEXT")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS picked_up BOOLEAN DEFAULT FALSE")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS estimated_hours FLOAT")
    op.execute("ALTER TABLE mc_tasks ADD COLUMN IF NOT EXISTS actual_hours FLOAT")

    # Create unique index on slug
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mc_tasks_slug ON mc_tasks(slug)")

    # Create index for project filtering
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_mc_tasks_project ON mc_tasks(project) WHERE project IS NOT NULL"
    )

    # Backfill slugs for existing rows
    op.execute("UPDATE mc_tasks SET slug = 'mc-' || id::text WHERE slug IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE mc_tasks SET slug = NULL")
    op.execute("DROP INDEX IF EXISTS idx_mc_tasks_project")
    op.execute("DROP INDEX IF EXISTS idx_mc_tasks_slug")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS slug")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS project")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS tags")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS skill")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS schedule")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS scheduled_at")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS references_")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS blocked_by")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS blocks")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS started_at")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS completed_at")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS result")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS error")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS picked_up")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS estimated_hours")
    op.execute("ALTER TABLE mc_tasks DROP COLUMN IF EXISTS actual_hours")
