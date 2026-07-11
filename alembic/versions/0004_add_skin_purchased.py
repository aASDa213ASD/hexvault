from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not _table_exists("skins"):
        return
    columns = _column_names("skins")
    if "purchased" in columns:
        return
    with op.batch_alter_table("skins") as batch_op:
        batch_op.add_column(sa.Column("purchased", sa.String(length=255), nullable=True))


def downgrade() -> None:
    if not _table_exists("skins"):
        return
    columns = _column_names("skins")
    if "purchased" not in columns:
        return
    with op.batch_alter_table("skins") as batch_op:
        batch_op.drop_column("purchased")


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()
