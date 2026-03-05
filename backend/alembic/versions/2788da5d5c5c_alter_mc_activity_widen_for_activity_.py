"""alter mc_activity widen for activity module

Revision ID: 2788da5d5c5c
Revises: ddde276426d8
Create Date: 2026-03-05 22:34:59.247359

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2788da5d5c5c"
down_revision: Union[str, Sequence[str], None] = "ddde276426d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE mc_activity ALTER COLUMN task_id DROP NOT NULL")
    op.execute("ALTER TABLE mc_activity ADD COLUMN IF NOT EXISTS resource_type TEXT")
    op.execute("ALTER TABLE mc_activity ADD COLUMN IF NOT EXISTS resource_id TEXT")
    op.execute("ALTER TABLE mc_activity ADD COLUMN IF NOT EXISTS resource_name TEXT")
    op.execute("ALTER TABLE mc_activity ADD COLUMN IF NOT EXISTS details JSONB DEFAULT '{}'")
    op.execute("ALTER TABLE mc_activity ADD COLUMN IF NOT EXISTS module TEXT")
    op.execute("ALTER TABLE mc_activity DROP CONSTRAINT IF EXISTS mc_activity_action_check")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_mc_activity_module ON mc_activity(module) WHERE module IS NOT NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS idx_mc_activity_module")
    op.execute("ALTER TABLE mc_activity DROP COLUMN IF EXISTS resource_type")
    op.execute("ALTER TABLE mc_activity DROP COLUMN IF EXISTS resource_id")
    op.execute("ALTER TABLE mc_activity DROP COLUMN IF EXISTS resource_name")
    op.execute("ALTER TABLE mc_activity DROP COLUMN IF EXISTS details")
    op.execute("ALTER TABLE mc_activity DROP COLUMN IF EXISTS module")
    op.execute("""
ALTER TABLE mc_activity ADD CONSTRAINT mc_activity_action_check
    CHECK (action = ANY (ARRAY['created'::text, 'state_changed'::text, 'assigned'::text,
        'commented'::text, 'reviewed'::text, 'approved'::text, 'rejected'::text]))
""")
    op.execute("UPDATE mc_activity SET task_id = 0 WHERE task_id IS NULL")
    op.execute("ALTER TABLE mc_activity ALTER COLUMN task_id SET NOT NULL")
