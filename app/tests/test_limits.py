from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Session, sessionmaker

from app.core.limits import (
    ANTI_FLOOD_SECONDS,
    DailyCapError,
    FloodError,
    ParallelismError,
    _track,
    consume,
)
from app.db import models
from app.db.base import Base
from app.db.models import Entitlement, Usage, User


def _setup_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    models.JSONB = SQLITE_JSON  # type: ignore[attr-defined]
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()


def _prepare_entitlement(session: Session) -> int:
    user = User(id=1, tg_id=1)
    session.add(user)
    session.commit()
    ent = Entitlement(
        id=1,
        user_id=user.id,
        product="pack_3",
        status="active",
        quota_total=2,
        quota_left=2,
        fair_daily_cap=1,
    )
    session.add(ent)
    session.commit()
    return user.id


def test_consume_records_usage_and_deducts_quota() -> None:
    session = _setup_session()
    user_id = _prepare_entitlement(session)
    consume(session, user_id=user_id, expert="tarot")
    ent = session.get(Entitlement, 1)
    assert ent is not None
    assert ent.quota_left == 1
    usage = session.query(Usage).one()
    assert usage.cost == 1


def test_consume_anti_flood_and_daily_cap() -> None:
    session = _setup_session()
    user_id = _prepare_entitlement(session)
    consume(session, user_id=user_id, expert="tarot")
    with pytest.raises(FloodError):
        consume(session, user_id=user_id, expert="tarot")
    # bypass anti-flood
    usage = session.query(Usage).first()
    assert usage is not None
    usage.created_at = datetime.utcnow() - timedelta(seconds=ANTI_FLOOD_SECONDS + 1)
    session.commit()
    with pytest.raises(DailyCapError):
        consume(session, user_id=user_id, expert="tarot")


def test_parallelism_limit() -> None:
    with _track(1):
        with _track(1):
            with pytest.raises(ParallelismError):
                with _track(1):
                    pass
