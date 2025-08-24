from __future__ import annotations

from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Event
from app.db.session import SessionLocal


class TelemetryEvent(str, Enum):
    """Enumeration of supported telemetry events."""

    START = "start"
    FORM_STEP = "form_step"
    DRAW_STARTED = "draw_started"
    WRITER_OK = "writer_ok"
    QUOTA_SPENT = "quota_spent"
    VERIFIER_OK = "verifier_ok"
    VERIFIER_FAIL = "verifier_fail"


def _store_event(
    session: Session,
    event: TelemetryEvent | str,
    *,
    user_id: int | None,
    props: dict[str, Any],
) -> None:
    row = Event(user_id=user_id, event=str(event), props_json=props)
    session.add(row)
    session.commit()


def track(
    event: TelemetryEvent | str,
    *,
    user_id: int | None = None,
    **props: Any,
) -> None:
    """Persist telemetry event to the database."""

    with SessionLocal() as session:
        _store_event(session, event, user_id=user_id, props=props)


__all__ = ["TelemetryEvent", "track"]
