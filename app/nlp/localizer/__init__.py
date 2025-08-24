from __future__ import annotations

from typing import Dict, List

_UI_STRINGS: Dict[str, Dict[str, str]] = {
    "welcome": {"en": "Welcome", "ru": "Добро пожаловать"},
    "submit": {"en": "Submit", "ru": "Отправить"},
}

_EXPERT_NAMES: Dict[str, Dict[str, str]] = {
    "tarot": {"en": "Tarot reader", "ru": "Таролог"},
    "runes": {"en": "Runes master", "ru": "Рунолог"},
}

_DISCLAIMERS: Dict[str, List[str]] = {
    "en": ["For entertainment purposes only."],
    "ru": ["Информация предоставлена исключительно в развлекательных целях."],
}


def get_ui_string(key: str, locale: str) -> str:
    return _UI_STRINGS.get(key, {}).get(locale, key)


def get_expert_name(expert: str, locale: str) -> str:
    return _EXPERT_NAMES.get(expert, {}).get(locale, expert)


def get_disclaimers(locale: str) -> List[str]:
    return _DISCLAIMERS.get(locale, _DISCLAIMERS["en"])
