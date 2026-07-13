from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not _table_exists("ranked_queues"):
        return

    if "days_until_decay" in _column_names("ranked_queues"):
        return

    with op.batch_alter_table("ranked_queues") as batch_op:
        batch_op.add_column(
            sa.Column("days_until_decay", sa.Integer(), nullable=True)
        )


def downgrade() -> None:
    if not _table_exists("ranked_queues"):
        return

    if "days_until_decay" not in _column_names("ranked_queues"):
        return

    with op.batch_alter_table("ranked_queues") as batch_op:
        batch_op.drop_column("days_until_decay")


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()
