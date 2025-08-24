from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image

from app.core.assets import ASSET_CACHE
from app.core.compose import CardSpec, Layout, save_image
from app.core.compose import compose as compose_cards
from app.core.draw import draw_unique
from app.core.plugins import Plugin
from app.experts.messages import get_actions, get_cta
from app.nlp.verifier import Verifier
from app.nlp.writer import compose_answer

PLUGIN_ID = "lenormand"


@dataclass(frozen=True)
class Spread:
    """Lenormand spread configuration."""

    spread_id: str
    layout: Layout
    captions: List[str]


SPREADS: Dict[str, Spread] = {
    "leno_three_line": Spread(
        "leno_three_line", Layout.ROW, [str(i) for i in range(1, 4)]
    ),
    "leno_five_line": Spread(
        "leno_five_line", Layout.ROW, [str(i) for i in range(1, 6)]
    ),
    "leno_nine_square": Spread(
        "leno_nine_square", Layout.GRID_3X3, [str(i) for i in range(1, 10)]
    ),
    "leno_grand_tableau_36": Spread(
        "leno_grand_tableau_36", Layout.GRAND_TABLEAU, [str(i) for i in range(1, 37)]
    ),
}


def form_steps(locale: str) -> list[dict[str, Any]]:
    """Input form steps for the Lenormand expert."""

    return [
        {"id": "deck_id", "type": "string"},
        {"id": "spread_id", "type": "string"},
        {"id": "question", "type": "string"},
    ]


def prepare(data: dict[str, Any]) -> dict[str, Any]:
    """Prepare deterministic draw and card metadata."""

    deck_id = data["deck_id"]
    spread_id = data["spread_id"]
    user_id = data.get("user_id", 0)
    draw_date = data.get("draw_date")
    if isinstance(draw_date, str):
        draw_date = date.fromisoformat(draw_date)
    elif draw_date is None:
        draw_date = date.today()
    nonce = int(data.get("nonce", 0))
    locale = data.get("locale", "en")

    deck_conf = ASSET_CACHE[deck_id]["config"]
    cards_manifest = deck_conf["cards"]
    pool = [c["key"] for c in cards_manifest]
    spread = SPREADS[spread_id]

    draw = draw_unique(
        pool,
        len(spread.captions),
        user_id=user_id,
        expert=PLUGIN_ID,
        spread_id=spread_id,
        draw_date=draw_date,
        nonce=nonce,
        allow_reversed=False,
    )

    by_key = {c["key"]: c for c in cards_manifest}
    cards: List[Dict[str, Any]] = []
    for item, caption in zip(draw, spread.captions, strict=True):
        info = by_key[item.key]
        cards.append(
            {
                "key": item.key,
                "file": info["file"],
                "display": info["display"],
                "caption": caption,
                "reversed": False,
            }
        )

    assets_root = Path(data.get("assets_root", "assets"))

    return {
        "deck_id": deck_id,
        "spread_id": spread_id,
        "spread": spread,
        "cards": cards,
        "locale": locale,
        "assets_root": str(assets_root),
    }


def compose(data: dict[str, Any]) -> dict[str, Any]:
    """Compose card collage with captions."""

    deck_id = data["deck_id"]
    spread: Spread = data["spread"]
    locale = data.get("locale", "en")
    assets_root = Path(data.get("assets_root", "assets"))
    deck_path = assets_root / "lenormand" / deck_id

    frame_img = None
    frame_path = deck_path / "frame.png"
    if frame_path.exists():
        frame_img = Image.open(frame_path)

    card_specs: List[CardSpec] = []
    names: List[str] = []
    for card in data["cards"]:
        img_path = deck_path / "cards" / card["file"]
        image = Image.open(img_path)
        name = card["display"].get(locale) or next(iter(card["display"].values()))
        names.append(name)
        caption = f"{card['caption']}: {name}"
        card_specs.append(CardSpec(image=image, caption=caption))

    collage = compose_cards(card_specs, spread.layout, frame=frame_img)
    image_bytes = save_image(collage, fmt="WEBP")
    facts = {f"card_{i + 1}": name for i, name in enumerate(names)}

    return {
        **data,
        "image": image_bytes,
        "image_format": "WEBP",
        "facts": facts,
    }


def write(data: dict[str, Any]) -> dict[str, Any]:
    """Generate textual reading and ensure factual accuracy."""

    locale = data.get("locale", "en")
    names = [name for name in data["facts"].values()]
    summary = ", ".join(names)
    details = "\n".join(f"{i + 1}. {name}" for i, name in enumerate(names))
    actions = get_actions(PLUGIN_ID, locale)

    facts = {
        **data["facts"],
        "summary": summary,
        "details": details,
        "actions": actions,
    }
    verifier = Verifier()
    output = verifier.ensure_verified(compose_answer, facts, locale)
    result: dict[str, Any] = output
    result["facts"] = data["facts"]
    return result


def verify(data: dict[str, Any]) -> bool:
    facts = data.get("facts", {})
    markdown = "\n".join(section["body_md"] for section in data.get("sections", []))
    verifier = Verifier()
    result = verifier.verify(facts, markdown)
    return bool(getattr(result, "ok", False))


def cta(locale: str) -> list[str]:
    return get_cta(PLUGIN_ID, locale)


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
