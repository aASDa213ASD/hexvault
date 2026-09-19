from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


COLUMNS = ("keys", "key_fragments", "chests")


def upgrade() -> None:
    if "loots" not in _table_names():
        return

    existing = _column_names("loots")
    for name in COLUMNS:
        if name not in existing:
            op.add_column(
                "loots",
                sa.Column(name, sa.Integer(), nullable=False, server_default="0"),
            )


def downgrade() -> None:
    if "loots" not in _table_names():
        return

    existing = _column_names("loots")
    for name in reversed(COLUMNS):
        if name in existing:
            op.drop_column("loots", name)


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _column_names(table_name: str) -> set[str]:
    return {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns(table_name)
    }
