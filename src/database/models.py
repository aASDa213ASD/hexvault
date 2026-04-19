from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_image_url: Mapped[str] = mapped_column(String(255))

    credentials: Mapped["Credentials"] = relationship(
        back_populates="account", cascade="all, delete-orphan", uselist=False
    )
    verification: Mapped["Verification"] = relationship(
        back_populates="account", cascade="all, delete-orphan", uselist=False
    )
    summoner: Mapped["Summoner"] = relationship(
        back_populates="account", cascade="all, delete-orphan", uselist=False
    )
    rank: Mapped["Rank"] = relationship(
        back_populates="account", cascade="all, delete-orphan", uselist=False
    )
    collection: Mapped["Collection"] = relationship(
        back_populates="account", cascade="all, delete-orphan", uselist=False
    )
    loot: Mapped["Loot"] = relationship(
        back_populates="account", cascade="all, delete-orphan", uselist=False
    )


class Credentials(Base):
    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String(255))
    password: Mapped[str] = mapped_column(String(255))
    account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"))

    account: Mapped[Account] = relationship(back_populates="credentials")


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean)
    account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"))

    account: Mapped[Account] = relationship(back_populates="verification")


class Summoner(Base):
    __tablename__ = "summoners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    summoner_account_id: Mapped[int] = mapped_column(Integer)
    summoner_id: Mapped[int] = mapped_column(Integer)
    puuid: Mapped[str] = mapped_column(String(255))
    region: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    tag: Mapped[str] = mapped_column(String(255))
    level: Mapped[int] = mapped_column(Integer)
    icon_id: Mapped[int] = mapped_column(Integer)
    icon_url: Mapped[str] = mapped_column(String(255))
    account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"))

    account: Mapped[Account] = relationship(back_populates="summoner")


class Rank(Base):
    __tablename__ = "ranks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"))

    account: Mapped[Account] = relationship(back_populates="rank")
    ranked_queues: Mapped[List["RankedQueue"]] = relationship(
        back_populates="rank", cascade="all, delete-orphan"
    )


class RankedQueue(Base):
    __tablename__ = "ranked_queues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(255))
    tier: Mapped[str] = mapped_column(String(255))
    division: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    league_points: Mapped[int] = mapped_column(Integer)
    wins: Mapped[int] = mapped_column(Integer)
    losses: Mapped[int] = mapped_column(Integer)
    icon_url: Mapped[str] = mapped_column(String(255))
    rank_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ranks.id"))

    rank: Mapped[Rank] = relationship(back_populates="ranked_queues")


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"))

    account: Mapped[Account] = relationship(back_populates="collection")
    champions: Mapped[List["Champion"]] = relationship(
        back_populates="collection", cascade="all, delete-orphan"
    )
    skins: Mapped[List["Skin"]] = relationship(
        back_populates="collection", cascade="all, delete-orphan"
    )


class Champion(Base):
    __tablename__ = "champions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    champion_id: Mapped[int] = mapped_column(Integer)
    alias: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    collection_id: Mapped[Optional[int]] = mapped_column(ForeignKey("collections.id"))
    splash_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    collection: Mapped[Collection] = relationship(back_populates="champions")


class Skin(Base):
    __tablename__ = "skins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skin_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    collection_id: Mapped[Optional[int]] = mapped_column(ForeignKey("collections.id"))

    collection: Mapped[Collection] = relationship(back_populates="skins")


class Loot(Base):
    __tablename__ = "loots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    blue_essence: Mapped[int] = mapped_column(Integer)
    orange_essence: Mapped[int] = mapped_column(Integer)
    riot_points: Mapped[int] = mapped_column(Integer)
    account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"))

    account: Mapped[Account] = relationship(back_populates="loot")
    champion_shards: Mapped[List["ChampionShard"]] = relationship(
        back_populates="loot", cascade="all, delete-orphan"
    )
    skin_shards: Mapped[List["SkinShard"]] = relationship(
        back_populates="loot", cascade="all, delete-orphan"
    )


class ChampionShard(Base):
    __tablename__ = "champion_shards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    amount: Mapped[int] = mapped_column(Integer)
    disenchant_value: Mapped[int] = mapped_column(Integer)
    upgrade_essence_value: Mapped[int] = mapped_column(Integer)
    is_already_owned: Mapped[bool] = mapped_column(Boolean)
    image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    loot_id: Mapped[Optional[int]] = mapped_column(ForeignKey("loots.id"))

    loot: Mapped[Loot] = relationship(back_populates="champion_shards")


class SkinShard(Base):
    __tablename__ = "skin_shards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    amount: Mapped[int] = mapped_column(Integer)
    disenchant_value: Mapped[int] = mapped_column(Integer)
    upgrade_essence_value: Mapped[int] = mapped_column(Integer)
    is_already_owned: Mapped[bool] = mapped_column(Boolean)
    image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    loot_id: Mapped[Optional[int]] = mapped_column(ForeignKey("loots.id"))

    loot: Mapped[Loot] = relationship(back_populates="skin_shards")
