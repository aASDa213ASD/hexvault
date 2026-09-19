from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


COLUMN = "champion_mastery_chests"


def upgrade() -> None:
    if "loots" not in _table_names() or COLUMN in _column_names("loots"):
        return

    op.add_column(
        "loots",
        sa.Column(COLUMN, sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    if "loots" not in _table_names() or COLUMN not in _column_names("loots"):
        return

    op.drop_column("loots", COLUMN)


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _column_names(table_name: str) -> set[str]:
    return {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns(table_name)
    }
