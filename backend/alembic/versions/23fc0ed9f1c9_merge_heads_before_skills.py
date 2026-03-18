"""merge_heads_before_skills

Revision ID: 23fc0ed9f1c9
Revises: 731ce699267c, cb0c373e0912
Create Date: 2026-03-18 20:20:36.409753

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "23fc0ed9f1c9"
down_revision: Union[str, Sequence[str], None] = ("731ce699267c", "cb0c373e0912")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
