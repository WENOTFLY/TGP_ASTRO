from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.nlp.localizer import get_disclaimers


class Section(BaseModel):
    title: str
    body_md: str


class WriterOutput(BaseModel):
    tldr: str = Field(..., max_length=280)
    sections: list[Section]
    actions: list[str]
    disclaimers: list[str]


def compose_answer(facts: dict[str, Any], locale: str) -> dict[str, Any]:
    """Compose a structured answer based on provided facts."""

    tldr = str(facts.get("summary", ""))
    sections_data = facts.get("sections")
    if not sections_data:
        detail = str(facts.get("details", ""))
        title = "Details" if locale == "en" else "Детали"
        sections_data = [{"title": title, "body_md": detail}]
    actions = [str(a) for a in facts.get("actions", [])]
    disclaimers = [str(d) for d in facts.get("disclaimers", [])]
    if not disclaimers:
        disclaimers = get_disclaimers(locale)
    output = WriterOutput(
        tldr=tldr,
        sections=[Section(**sec) for sec in sections_data],
        actions=actions,
        disclaimers=disclaimers,
    )
    return output.model_dump()
