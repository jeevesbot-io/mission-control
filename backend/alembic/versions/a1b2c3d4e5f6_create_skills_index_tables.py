"""create skills_index and skills_drift_log tables

Revision ID: a1b2c3d4e5f6
Revises: 23fc0ed9f1c9
Create Date: 2026-03-18 20:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str]] = "23fc0ed9f1c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skills_index",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("skill_name", sa.Text(), nullable=False),
        sa.Column("source_dir", sa.Text(), nullable=False),
        sa.Column("source_label", sa.Text(), nullable=False),
        sa.Column("skill_path", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("homepage", sa.Text(), nullable=True),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("sha256_hash", sa.Text(), nullable=False),
        sa.Column("frontmatter", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "last_indexed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_path"),
    )
    op.create_index("idx_skills_source", "skills_index", ["source_label"])
    op.create_index("idx_skills_name", "skills_index", ["skill_name"])
    op.create_index("idx_skills_changed", "skills_index", ["last_changed_at"])

    op.create_table(
        "skills_drift_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("old_hash", sa.Text(), nullable=False),
        sa.Column("new_hash", sa.Text(), nullable=False),
        sa.Column("old_file_count", sa.Integer(), nullable=True),
        sa.Column("new_file_count", sa.Integer(), nullable=True),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("files_changed", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills_index.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_drift_skill", "skills_drift_log", ["skill_id"])
    op.create_index("idx_drift_detected", "skills_drift_log", ["detected_at"])


def downgrade() -> None:
    op.drop_table("skills_drift_log")
    op.drop_table("skills_index")
