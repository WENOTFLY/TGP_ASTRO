from __future__ import annotations

from typing import Dict, List

ACTIONS: Dict[str, Dict[str, List[str]]] = {
    "tarot": {
        "en": [
            "Reflect on how the cards relate to your question.",
            "Trust your intuition as you interpret the spread.",
            "Record your insights for future reference.",
        ],
        "ru": [
            "Подумайте, как карты связаны с вашим вопросом.",
            "Доверьтесь интуиции, интерпретируя расклад.",
            "Запишите инсайты для будущего.",
        ],
    },
    "runes": {
        "en": [
            "Reflect on how the runes relate to your question.",
            "Trust your intuition as you interpret their meanings.",
            "Record your insights for future reference.",
        ],
        "ru": [
            "Подумайте, как руны связаны с вашим вопросом.",
            "Доверьтесь интуиции при трактовке значения.",
            "Запишите инсайты для будущего.",
        ],
    },
    "lenormand": {
        "en": [
            "Note the sequence of cards.",
            "Consider how each card relates to your question.",
            "Record your insights for later.",
        ],
        "ru": [
            "Обратите внимание на порядок карт.",
            "Подумайте, как каждая карта связана с вашим вопросом.",
            "Запишите свои мысли для будущего.",
        ],
    },
    "assistant": {
        "en": [
            "Check the response.",
            "Ask follow-up questions.",
            "Apply the suggestions.",
        ],
        "ru": [
            "Проверьте ответ.",
            "Задайте уточняющие вопросы.",
            "Примените предложения.",
        ],
    },
    "copywriter": {
        "en": [
            "Outline main points.",
            "Draft the text.",
            "Edit and publish.",
        ],
        "ru": [
            "Определите основные тезисы.",
            "Подготовьте черновик.",
            "Отредактируйте и опубликуйте.",
        ],
    },
    "dreams": {
        "en": [
            "Keep a dream journal.",
            "Reflect on the feelings in the dream.",
            "Share the dream with someone you trust.",
        ],
        "ru": [
            "Ведите дневник снов.",
            "Подумайте, какие чувства вызвал сон.",
            "Поделитесь сном с близким человеком.",
        ],
    },
    "numerology": {
        "en": [
            "Reflect on these numbers.",
            "Keep a journal.",
            "Share with a friend.",
        ],
        "ru": [
            "Подумайте над этими числами.",
            "Ведите дневник.",
            "Поделитесь с другом.",
        ],
    },
    "astrology": {
        "en": [
            "Reflect on these planetary placements.",
            "Consider how aspects influence your chart.",
            "Use this insight for self-awareness.",
        ],
        "ru": [
            "Обдумайте эти положения планет.",
            "Подумайте, как аспекты влияют на вашу карту.",
            "Используйте это понимание для самопознания.",
        ],
    },
}

CTA: Dict[str, Dict[str, List[str]]] = {
    "tarot": {
        "en": ["Draw another card", "Try another spread", "Share"],
        "ru": ["Дотянуть карту", "Другой спред", "Поделиться"],
    },
    "runes": {
        "en": ["Draw another rune", "Try another spread", "Share"],
        "ru": ["Дотянуть руну", "Другой расклад", "Поделиться"],
    },
    "lenormand": {
        "en": ["Draw again", "Try another spread", "Share"],
        "ru": ["Перетянуть", "Другой расклад", "Поделиться"],
    },
    "assistant": {
        "en": ["Refine", "New request", "Share"],
        "ru": ["Уточнить", "Новый запрос", "Поделиться"],
    },
    "copywriter": {
        "en": ["Clarify", "Try another topic", "Share"],
        "ru": ["Уточнить", "Другая тема", "Поделиться"],
    },
    "dreams": {
        "en": ["Interpret another dream", "Share"],
        "ru": ["Расшифровать другой сон", "Поделиться"],
    },
    "numerology": {
        "en": ["Try another date", "Share"],
        "ru": ["Другую дату", "Поделиться"],
    },
    "astrology": {
        "en": ["Calculate again", "Share"],
        "ru": ["Рассчитать снова", "Поделиться"],
    },
}

DISCLAIMERS: Dict[str, Dict[str, List[str]]] = {
    "runes": {
        "en": ["For entertainment purposes only."],
        "ru": ["Только для развлечения."],
    },
    "dreams": {
        "en": ["This interpretation is for entertainment and not medical advice."],
        "ru": [
            "Толкование носит развлекательный характер и не является "
            "медицинской помощью."
        ],
    },
    "astrology": {
        "en": ["Birth time unknown; chart is calculated for solar noon."],
        "ru": ["Время рождения неизвестно; карта построена на полдень."],
    },
}

SECTION_TITLES: Dict[str, Dict[str, Dict[str, str]]] = {
    "assistant": {
        "request": {"en": "Request", "ru": "Запрос"},
        "details": {"en": "Details", "ru": "Детали"},
    },
    "copywriter": {
        "theme": {"en": "Theme", "ru": "Тема"},
        "brief": {"en": "Brief", "ru": "Бриф"},
    },
}


def get_actions(expert: str, locale: str) -> List[str]:
    return ACTIONS.get(expert, {}).get(locale, ACTIONS.get(expert, {}).get("en", []))


def get_cta(expert: str, locale: str) -> List[str]:
    return CTA.get(expert, {}).get(locale, CTA.get(expert, {}).get("en", []))


def get_disclaimers(expert: str, locale: str) -> List[str]:
    return DISCLAIMERS.get(expert, {}).get(
        locale, DISCLAIMERS.get(expert, {}).get("en", [])
    )


def get_section_title(expert: str, section: str, locale: str) -> str:
    sect = SECTION_TITLES.get(expert, {}).get(section, {})
    return sect.get(locale, sect.get("en", section))
