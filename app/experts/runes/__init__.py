from __future__ import annotations

import importlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image

from app.core.assets import ASSET_CACHE
from app.core.draw import draw_unique
from app.core.plugins import Plugin
from app.nlp.verifier import Verifier
from app.nlp.writer import compose_answer

compose_mod = importlib.import_module("app.core.compose")
CardSpec: Any = compose_mod.CardSpec
Layout: Any = compose_mod.Layout
compose_cards = compose_mod.compose
save_image = compose_mod.save_image

PLUGIN_ID = "runes"


@dataclass(frozen=True)
class Spread:
    """Runes spread configuration."""

    spread_id: str
    layout: Layout
    captions: List[str]


SPREADS: Dict[str, Spread] = {
    "runes_one": Spread("runes_one", Layout.ROW, ["Rune"]),
    "runes_three_ppf": Spread(
        "runes_three_ppf", Layout.ROW, ["Past", "Present", "Future"]
    ),
    "runes_five_cross": Spread(
        "runes_five_cross",
        Layout.CROSS,
        ["Situation", "Challenge", "Advice", "Outcome", "Root"],
    ),
}


def form_steps(locale: str) -> list[dict[str, Any]]:
    """Input form steps for the runes expert."""

    return [
        {"id": "set_id", "type": "string"},
        {"id": "spread_id", "type": "string"},
        {"id": "question", "type": "string"},
    ]


def prepare(data: dict[str, Any]) -> dict[str, Any]:
    """Prepare deterministic rune draw and metadata."""

    set_id = data["set_id"]
    spread_id = data["spread_id"]
    user_id = data.get("user_id", 0)
    draw_date = data.get("draw_date")
    if isinstance(draw_date, str):
        draw_date = date.fromisoformat(draw_date)
    elif draw_date is None:
        draw_date = date.today()
    nonce = int(data.get("nonce", 0))
    locale = data.get("locale", "en")

    set_conf = ASSET_CACHE[set_id]["config"]
    runes_manifest = set_conf["runes"]
    pool = [r["key"] for r in runes_manifest]
    allow_reversed = bool(set_conf.get("image", {}).get("allow_reversed", False))
    spread = SPREADS[spread_id]

    draw = draw_unique(
        pool,
        len(spread.captions),
        user_id=user_id,
        expert=PLUGIN_ID,
        spread_id=spread_id,
        draw_date=draw_date,
        nonce=nonce,
        allow_reversed=allow_reversed,
        p_reversed=0.33,
    )

    by_key = {r["key"]: r for r in runes_manifest}
    runes: List[Dict[str, Any]] = []
    for item, caption in zip(draw, spread.captions, strict=True):
        info = by_key[item.key]
        can_reverse = bool(info.get("can_reverse", True))
        runes.append(
            {
                "key": item.key,
                "file": info["file"],
                "display": info["display"],
                "caption": caption,
                "reversed": item.reversed if can_reverse else False,
            }
        )

    assets_root = Path(data.get("assets_root", "assets"))

    return {
        "set_id": set_id,
        "spread_id": spread_id,
        "spread": spread,
        "runes": runes,
        "locale": locale,
        "assets_root": str(assets_root),
    }


def compose(data: dict[str, Any]) -> dict[str, Any]:
    """Compose rune collage with captions."""

    set_id = data["set_id"]
    spread: Spread = data["spread"]
    locale = data.get("locale", "en")
    assets_root = Path(data.get("assets_root", "assets"))
    set_path = assets_root / "runes" / set_id

    frame_img = None
    frame_path = set_path / "frame.png"
    if frame_path.exists():
        frame_img = Image.open(frame_path)

    rune_specs: List[CardSpec] = []
    names: List[str] = []
    orientations: List[str] = []
    for rune in data["runes"]:
        img_path = set_path / "runes" / rune["file"]
        image = Image.open(img_path)
        name = rune["display"].get(locale) or next(iter(rune["display"].values()))
        names.append(name)
        orientation = "reversed" if rune["reversed"] else "upright"
        orientations.append(orientation)
        caption = f"{rune['caption']}: {name}"
        rune_specs.append(
            CardSpec(image=image, caption=caption, reversed=rune["reversed"])
        )

    collage = compose_cards(rune_specs, spread.layout, frame=frame_img)
    image_bytes = save_image(collage, fmt="WEBP")

    facts: Dict[str, Any] = {}
    for i, (name, orientation) in enumerate(
        zip(names, orientations, strict=True), start=1
    ):
        facts[f"rune_{i}"] = name
        facts[f"rune_{i}_orientation"] = orientation

    return {
        **data,
        "image": image_bytes,
        "image_format": "WEBP",
        "facts": facts,
    }


def write(data: dict[str, Any]) -> dict[str, Any]:
    """Generate textual reading for runes and verify facts."""

    locale = data.get("locale", "en")
    facts = data["facts"]
    count = len([k for k in facts if k.startswith("rune_") and "_orientation" not in k])
    names = [facts[f"rune_{i}"] for i in range(1, count + 1)]
    summary = ", ".join(names)

    sections: List[Dict[str, str]] = []
    for i in range(1, count + 1):
        name = facts[f"rune_{i}"]
        orientation = facts[f"rune_{i}_orientation"]
        body = f"The {name} rune appears {orientation}."
        sections.append({"title": name, "body_md": body})

    actions = [
        "Reflect on how the runes relate to your question.",
        "Trust your intuition as you interpret their meanings.",
        "Record your insights for future reference.",
    ]
    disclaimers = ["For entertainment purposes only."]

    verify_facts = {
        **facts,
        "summary": summary,
        "sections": sections,
        "actions": actions,
        "disclaimers": disclaimers,
    }
    verifier = Verifier()
    output = verifier.ensure_verified(compose_answer, verify_facts, locale)
    result: dict[str, Any] = output
    result["facts"] = facts
    return result


def verify(data: dict[str, Any]) -> bool:
    facts = data.get("facts", {})
    markdown = "\n".join(section["body_md"] for section in data.get("sections", []))
    verifier = Verifier()
    result = verifier.verify(facts, markdown)
    return bool(getattr(result, "ok", False))


def cta(locale: str) -> list[str]:
    return ["Draw another rune", "Try another spread", "Share"]


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
