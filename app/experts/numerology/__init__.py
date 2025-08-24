from __future__ import annotations

from typing import Any

from app.core.plugins import Plugin

PLUGIN_ID = "numerology"


def form_steps(locale: str) -> list[dict[str, Any]]:
    return []


def prepare(data: dict[str, Any]) -> dict[str, Any]:
    return data


def compose(data: dict[str, Any]) -> dict[str, Any]:
    return data


def write(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "tldr": "Numerology plugin response",
        "sections": [],
        "actions": [],
        "disclaimers": [],
    }


def verify(data: dict[str, Any]) -> bool:
    return True


def cta(locale: str) -> list[str]:
    return []


plugin = Plugin(
    plugin_id=PLUGIN_ID,
    form_steps=form_steps,
    prepare=prepare,
    compose=compose,
    write=write,
    verify=verify,
    cost=0,
    cta=cta,
    products_supported=("basic",),
)
