from __future__ import annotations

from typing import Dict

_HINTS: Dict[str, Dict[str, Dict[str, str]]] = {
    "tarot": {
        "intro": {
            "en": "Focus on your question for the cards.",
            "ru": "Сконцентрируйтесь на своём вопросе для карт.",
        },
        "shuffle": {
            "en": "Shuffle the deck in your mind.",
            "ru": "Перетасуйте колоду мысленно.",
        },
    },
    "runes": {
        "intro": {
            "en": "Calm your mind before drawing runes.",
            "ru": "Успокойте мысли перед вытягиванием рун.",
        }
    },
}


def get_tip(expert: str, step: str, locale: str) -> dict[str, str]:
    """Return a short tip for a given expert step and locale."""

    expert_hints = _HINTS.get(expert, {})
    step_hints = expert_hints.get(step, {})
    tip = step_hints.get(locale) or step_hints.get("en") or ""
    return {"tip": tip}


def register_tip(expert: str, step: str, locale: str, tip: str) -> None:
    """Register or override a tip."""

    _HINTS.setdefault(expert, {}).setdefault(step, {})[locale] = tip
