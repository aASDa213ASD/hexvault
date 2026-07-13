from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Some databases were created with SQLAlchemy's metadata before Alembic
    # was introduced.  They can already have this column while still being
    # stamped at an older revision (or at 0001 during bootstrap).
    if "accounts" not in _table_names():
        return
    if "notes" in _column_names("accounts"):
        return

    op.add_column(
        "accounts",
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    if "accounts" not in _table_names() or "notes" not in _column_names("accounts"):
        return

    op.drop_column("accounts", "notes")


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}
