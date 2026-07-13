from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from alembic import op
import sqlalchemy as sa


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not _table_exists("ranked_queues"):
        return

    if "decay_deadline" in _column_names("ranked_queues"):
        return

    with op.batch_alter_table("ranked_queues") as batch_op:
        batch_op.add_column(
            sa.Column("decay_deadline", sa.DateTime(timezone=True), nullable=True)
        )

    _backfill_decay_deadlines()


def downgrade() -> None:
    if not _table_exists("ranked_queues"):
        return

    if "decay_deadline" not in _column_names("ranked_queues"):
        return

    with op.batch_alter_table("ranked_queues") as batch_op:
        batch_op.drop_column("decay_deadline")


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _backfill_decay_deadlines() -> None:
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
        ).where(
            ranked_queues.c.days_until_decay.is_not(None),
            ranked_queues.c.decay_deadline.is_(None),
        )
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
