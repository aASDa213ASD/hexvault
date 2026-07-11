from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

TABLE_COLUMNS = {
    "accounts": (
        ("account_image_url", sa.String(length=255), True),
    ),
    "champions": (
        ("image_url", sa.String(length=255), True),
        ("splash_url", sa.String(length=255), True),
    ),
    "skins": (
        ("image_url", sa.String(length=255), True),
    ),
    "champion_shards": (
        ("image_url", sa.String(length=255), True),
    ),
    "skin_shards": (
        ("image_url", sa.String(length=255), True),
    ),
    "ranked_queues": (
        ("icon_url", sa.String(length=255), True),
    ),
}


def upgrade() -> None:
    for table_name, column_specs in TABLE_COLUMNS.items():
        columns = _column_names(table_name)
        columns_to_drop = [
            column_name
            for column_name, _column_type, _nullable in column_specs
            if column_name in columns
        ]
        if not columns_to_drop:
            continue

        with op.batch_alter_table(table_name) as batch_op:
            for column in columns_to_drop:
                batch_op.drop_column(column)


def downgrade() -> None:
    for table_name, column_specs in reversed(TABLE_COLUMNS.items()):
        columns = _column_names(table_name)
        with op.batch_alter_table(table_name) as batch_op:
            for column_name, column_type, nullable in column_specs:
                if column_name not in columns:
                    batch_op.add_column(
                        sa.Column(column_name, column_type, nullable=nullable)
                    )


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}
