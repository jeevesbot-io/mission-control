"""Add docs column to mc_projects

Revision ID: a1b2c3d4e5f6
Revises: 731ce699267c
Create Date: 2026-03-09 20:15:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "731ce699267c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("mc_projects", sa.Column("docs", JSONB, server_default="[]", nullable=False))


def downgrade() -> None:
    op.drop_column("mc_projects", "docs")
