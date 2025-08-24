from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image

from app.core.compose import CardSpec, Layout, compose as compose_cards, save_image
from app.core.plugins import Plugin
from app.nlp.verifier import Verifier
from app.nlp.writer import compose_answer

PLUGIN_ID = "dreams"


def form_steps(locale: str) -> list[dict[str, Any]]:
    """Input form for dream interpretation."""

    return [{"id": "dream", "type": "string"}]


def _load_lexicon(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def prepare(data: dict[str, Any]) -> dict[str, Any]:
    """Parse dream text and extract symbols from lexicon."""

    dream_text = str(data.get("dream", ""))
    locale = data.get("locale", "en")
    assets_root = Path(data.get("assets_root", "assets"))
    lexicon_path = assets_root / "dreams" / "lexicon.json"
    lexicon = _load_lexicon(lexicon_path)

    text = dream_text.lower()
    symbols: List[Dict[str, Any]] = []
    for key, info in lexicon.items():
        synonyms = [key] + list(info.get("synonyms", []))
        for syn in synonyms:
            pattern = r"\b" + re.escape(syn.lower()) + r"\b"
            if re.search(pattern, text):
                symbols.append({"key": key, **info})
                break

    return {
        "dream": dream_text,
        "symbols": symbols,
        "locale": locale,
        "assets_root": str(assets_root),
    }


def compose(data: dict[str, Any]) -> dict[str, Any]:
    """Compose collage of dream symbols."""

    assets_root = Path(data.get("assets_root", "assets"))
    locale = data.get("locale", "en")
    symbols = data.get("symbols", [])

    specs: List[CardSpec] = []
    facts: Dict[str, Any] = {}

    for i, symbol in enumerate(symbols, start=1):
        file = symbol.get("file")
        if file:
            img_path = assets_root / "dreams" / "symbols" / file
            try:
                img = Image.open(img_path)
            except FileNotFoundError:
                img = Image.new("RGB", (200, 200), (200, 200, 200))
        else:
            img = Image.new("RGB", (200, 200), (200, 200, 200))
        name = symbol.get("display", {}).get(locale) or next(
            iter(symbol.get("display", {}).values()),
            symbol["key"].capitalize(),
        )
        meaning = symbol.get("meaning", {}).get(locale) or next(
            iter(symbol.get("meaning", {}).values()),
            "",
        )
        specs.append(CardSpec(image=img, caption=name, reversed=False))
        facts[f"symbol_{i}"] = name
        facts[f"symbol_{i}_meaning"] = meaning

    if specs:
        collage = compose_cards(specs, Layout.ROW)
    else:
        collage = Image.new("RGB", (1, 1), (255, 255, 255))
    image_bytes = save_image(collage, fmt="WEBP")

    return {
        **data,
        "image": image_bytes,
        "image_format": "WEBP",
        "facts": facts,
    }


def write(data: dict[str, Any]) -> dict[str, Any]:
    """Generate textual interpretation with disclaimers."""

    locale = data.get("locale", "en")
    facts = data.get("facts", {})

    names = [
        v
        for k, v in facts.items()
        if k.startswith("symbol_") and not k.endswith("_meaning")
    ]
    summary = ", ".join(names)

    sections: List[Dict[str, str]] = []
    i = 1
    while f"symbol_{i}" in facts:
        name = facts[f"symbol_{i}"]
        meaning = facts.get(f"symbol_{i}_meaning", "")
        body = f"{name}: {meaning}" if meaning else name
        sections.append({"title": name, "body_md": body})
        i += 1

    if locale == "ru":
        actions = [
            "Ведите дневник снов.",
            "Подумайте, какие чувства вызвал сон.",
            "Поделитесь сном с близким человеком.",
        ]
        disclaimers = [
            "Толкование носит развлекательный характер и не является медицинской помощью."
        ]
    else:
        actions = [
            "Keep a dream journal.",
            "Reflect on the feelings in the dream.",
            "Share the dream with someone you trust.",
        ]
        disclaimers = [
            "This interpretation is for entertainment and not medical advice."
        ]

    verify_facts = {
        **facts,
        "summary": summary,
        "sections": sections,
        "actions": actions,
        "disclaimers": disclaimers,
    }
    verifier = Verifier()
    output = verifier.ensure_verified(compose_answer, verify_facts, locale)
    result: Dict[str, Any] = output
    result["facts"] = facts
    return result


def verify(data: dict[str, Any]) -> bool:
    facts = data.get("facts", {})
    markdown = "\n".join(section["body_md"] for section in data.get("sections", []))
    verifier = Verifier()
    result = verifier.verify(facts, markdown)
    return bool(getattr(result, "ok", False))


def cta(locale: str) -> list[str]:
    return [
        "Interpret another dream" if locale == "en" else "Расшифровать другой сон",
        "Share",
    ]


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
