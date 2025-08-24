from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from sqlalchemy.orm import Session

from app.db.models import Entitlement, Usage

ANTI_FLOOD_SECONDS = 3


class QuotaError(Exception):
    """Raised when user has insufficient quota."""


class DailyCapError(Exception):
    """Raised when fair daily cap is exceeded."""


class FloodError(Exception):
    """Raised on too frequent requests."""


class ParallelismError(Exception):
    """Raised when user runs too many parallel operations."""


_inflight: dict[int, int] = defaultdict(int)


@contextmanager
def _track(user_id: int) -> Iterator[None]:
    count = _inflight[user_id]
    if count >= 2:
        raise ParallelismError("too many parallel operations")
    _inflight[user_id] = count + 1
    try:
        yield
    finally:
        _inflight[user_id] -= 1


def consume(session: Session, user_id: int, expert: str, cost: int = 1) -> None:
    """Consume quota for the given user and record usage."""

    with _track(user_id):
        now = datetime.utcnow()
        entitlement = (
            session.query(Entitlement)
            .filter(Entitlement.user_id == user_id, Entitlement.status == "active")
            .order_by(Entitlement.created_at.desc())
            .first()
        )
        if entitlement is None or (
            entitlement.expires_at and entitlement.expires_at < now
        ):
            raise QuotaError("no active entitlement")
        if entitlement.quota_left > 0 and entitlement.quota_left < cost:
            raise QuotaError("not enough quota")
        last_usage = (
            session.query(Usage)
            .filter(Usage.user_id == user_id)
            .order_by(Usage.created_at.desc())
            .first()
        )
        if (
            last_usage
            and (now - last_usage.created_at).total_seconds() < ANTI_FLOOD_SECONDS
        ):
            raise FloodError("too frequent requests")
        start_day = datetime(now.year, now.month, now.day)
        today_count = (
            session.query(Usage)
            .filter(Usage.user_id == user_id, Usage.created_at >= start_day)
            .count()
        )
        if entitlement.fair_daily_cap and today_count >= entitlement.fair_daily_cap:
            raise DailyCapError("daily cap reached")
        if entitlement.quota_left > 0:
            entitlement.quota_left -= cost
        session.add(
            Usage(
                id=int(now.timestamp() * 1000),
                user_id=user_id,
                expert=expert,
                cost=cost,
            )
        )
        session.commit()
