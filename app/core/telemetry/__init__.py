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
    FORM_STARTED = "form_started"
    FORM_COMPLETED = "form_completed"
    DRAW_STARTED = "draw_started"
    GENERATION_STARTED = "generation_started"
    GENERATION_COMPLETED = "generation_completed"
    WRITER_OK = "writer_ok"
    DELIVERY_STARTED = "delivery_started"
    DELIVERY_COMPLETED = "delivery_completed"
    QUOTA_SPENT = "quota_spent"
    VERIFIER_OK = "verifier_ok"
    VERIFIER_FAIL = "verifier_fail"
    CTA_CLICK = "cta_click"


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
