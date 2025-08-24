from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    desc,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tg_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    username: Mapped[str | None] = mapped_column(String)
    locale: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    name_raw: Mapped[str | None] = mapped_column(String)
    name_norm: Mapped[str | None] = mapped_column(String)
    dob_date: Mapped[date | None] = mapped_column(Date)
    birth_time: Mapped[time | None] = mapped_column(Time)
    birth_place: Mapped[str | None] = mapped_column(String)
    tz: Mapped[str | None] = mapped_column(String)
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    product: Mapped[str] = mapped_column(String, nullable=False)
    amount_xtr: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    external_id: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Entitlement(Base):
    __tablename__ = "entitlements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    product: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    quota_total: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    quota_left: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    fair_daily_cap: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_entitlements_user_id_status", "user_id", "status"),)


class Usage(Base):
    __tablename__ = "usages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expert: Mapped[str] = mapped_column(String, nullable=False)
    cost: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    name_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Draw(Base):
    __tablename__ = "draws"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expert: Mapped[str] = mapped_column(String, nullable=False)
    deck_id: Mapped[str] = mapped_column(String, nullable=False)
    spread_id: Mapped[str] = mapped_column(String, nullable=False)
    seed: Mapped[str] = mapped_column(String, nullable=False)
    facts_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_draws_user_id_created_at", "user_id", desc("created_at")),
    )


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expert: Mapped[str] = mapped_column(String, nullable=False)
    input_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    facts_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    text_md: Mapped[str | None] = mapped_column(String)
    pdf_url: Mapped[str | None] = mapped_column(String)
    images_json: Mapped[dict[str, Any] | list[Any]] = mapped_column(
        JSONB, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    event: Mapped[str] = mapped_column(String, nullable=False)
    props_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_events_ts_event", "ts", "event"),)
