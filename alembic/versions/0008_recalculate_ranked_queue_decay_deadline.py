from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from alembic import op
import sqlalchemy as sa


revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not _table_exists("ranked_queues"):
        return

    columns = _column_names("ranked_queues")
    if not {"days_until_decay", "decay_deadline"}.issubset(columns):
        return

    _recalculate_decay_deadlines()


def downgrade() -> None:
    pass


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _recalculate_decay_deadlines() -> None:
    ranked_queues = sa.table(
        "ranked_queues",
        sa.column("id", sa.Integer),
        sa.column("days_until_decay", sa.Integer),
        sa.column("decay_deadline", sa.DateTime(timezone=True)),
    )
    connection = op.get_bind()
    rows = connection.execute(
        sa.select(
            ranked_queues.c.id,
            ranked_queues.c.days_until_decay,
        ).where(ranked_queues.c.days_until_decay.is_not(None))
    )

    now = datetime.now().astimezone()
    for row in rows:
        local_midnight = datetime.combine(
            now.date() + timedelta(days=max(int(row.days_until_decay), 0)),
            time.min,
            tzinfo=now.tzinfo,
        )
        connection.execute(
            ranked_queues.update()
            .where(ranked_queues.c.id == row.id)
            .values(decay_deadline=local_midnight.astimezone(timezone.utc))
        )
