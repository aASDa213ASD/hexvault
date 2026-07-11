from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("account_image_url", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "collections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "credentials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("login", sa.String(length=255), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "loots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("blue_essence", sa.Integer(), nullable=False),
        sa.Column("orange_essence", sa.Integer(), nullable=False),
        sa.Column("riot_points", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ranks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "summoners",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("summoner_account_id", sa.Integer(), nullable=False),
        sa.Column("summoner_id", sa.Integer(), nullable=False),
        sa.Column("puuid", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("tag", sa.String(length=255), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("icon_id", sa.Integer(), nullable=False),
        sa.Column("icon_url", sa.String(length=255), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "verifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=255), nullable=True),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False),
        sa.Column("is_phone_verified", sa.Boolean(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "champions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("champion_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("image_url", sa.String(length=255), nullable=True),
        sa.Column("collection_id", sa.Integer(), nullable=True),
        sa.Column("splash_url", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ranked_queues",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("tier", sa.String(length=255), nullable=False),
        sa.Column("division", sa.String(length=255), nullable=True),
        sa.Column("league_points", sa.Integer(), nullable=False),
        sa.Column("wins", sa.Integer(), nullable=False),
        sa.Column("losses", sa.Integer(), nullable=False),
        sa.Column("icon_url", sa.String(length=255), nullable=False),
        sa.Column("rank_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["rank_id"], ["ranks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "skins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("skin_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("image_url", sa.String(length=255), nullable=True),
        sa.Column("collection_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "champion_shards",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("disenchant_value", sa.Integer(), nullable=False),
        sa.Column("upgrade_essence_value", sa.Integer(), nullable=False),
        sa.Column("is_already_owned", sa.Boolean(), nullable=False),
        sa.Column("image_url", sa.String(length=255), nullable=True),
        sa.Column("loot_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["loot_id"], ["loots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "skin_shards",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("disenchant_value", sa.Integer(), nullable=False),
        sa.Column("upgrade_essence_value", sa.Integer(), nullable=False),
        sa.Column("is_already_owned", sa.Boolean(), nullable=False),
        sa.Column("image_url", sa.String(length=255), nullable=True),
        sa.Column("loot_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["loot_id"], ["loots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("skin_shards")
    op.drop_table("champion_shards")
    op.drop_table("skins")
    op.drop_table("ranked_queues")
    op.drop_table("champions")
    op.drop_table("verifications")
    op.drop_table("summoners")
    op.drop_table("ranks")
    op.drop_table("loots")
    op.drop_table("credentials")
    op.drop_table("collections")
    op.drop_table("accounts")
