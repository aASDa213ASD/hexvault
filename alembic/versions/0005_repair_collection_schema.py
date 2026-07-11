from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


REPAIRS = {
    "champions": {
        "add": (
            ("purchased", sa.String(length=255), True),
        ),
        "drop": ("title", "image_url", "splash_url"),
    },
    "skins": {
        "add": (
            ("purchased", sa.String(length=255), True),
        ),
        "drop": ("title", "image_url"),
    },
}


def upgrade() -> None:
    for table_name, repair in REPAIRS.items():
        if not _table_exists(table_name):
            continue

        columns = _column_names(table_name)
        columns_to_add = [
            column
            for column in repair["add"]
            if column[0] not in columns
        ]
        columns_to_drop = [
            column
            for column in repair["drop"]
            if column in columns
        ]
        if not columns_to_add and not columns_to_drop:
            continue

        with op.batch_alter_table(table_name) as batch_op:
            for column_name, column_type, nullable in columns_to_add:
                batch_op.add_column(
                    sa.Column(column_name, column_type, nullable=nullable)
                )
            for column_name in columns_to_drop:
                batch_op.drop_column(column_name)


def downgrade() -> None:
    pass


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()
