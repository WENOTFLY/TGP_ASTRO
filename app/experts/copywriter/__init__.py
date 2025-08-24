from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.core.compose import save_image
from app.core.draw import draw_unique
from app.core.plugins import Plugin
from app.experts.messages import get_actions, get_cta, get_section_title
from app.nlp.verifier import Verifier
from app.nlp.writer import compose_answer

PLUGIN_ID = "copywriter"


def form_steps(locale: str) -> list[dict[str, Any]]:
    """Collect theme and optional brief from user."""

    return [
        {"id": "theme", "type": "string"},
        {"id": "brief", "type": "string", "optional": True},
    ]


def prepare(data: dict[str, Any]) -> dict[str, Any]:
    """Select optional banner asset deterministically."""

    theme = str(data["theme"])
    brief = str(data.get("brief", ""))
    assets_root = Path(data.get("assets_root", "assets"))
    banner_asset = data.get("banner_asset")
    banner_path: Path | None = None
    if banner_asset:
        banner_path = assets_root / banner_asset
    else:
        banner_dir = assets_root / "banners"
        if banner_dir.exists():
            pool = [
                p.name
                for p in banner_dir.iterdir()
                if p.is_file()
                and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
            ]
            if pool:
                user_id = data.get("user_id", 0)
                draw_date = data.get("draw_date")
                if isinstance(draw_date, str):
                    draw_date = date.fromisoformat(draw_date)
                elif draw_date is None:
                    draw_date = date.today()
                nonce = int(data.get("nonce", 0))
                pick = draw_unique(
                    pool,
                    1,
                    user_id=user_id,
                    expert=PLUGIN_ID,
                    spread_id="banner",
                    draw_date=draw_date,
                    nonce=nonce,
                )[0]
                banner_path = banner_dir / pick.key
    return {
        "theme": theme,
        "brief": brief,
        "banner_asset": str(banner_path) if banner_path else None,
        "assets_root": str(assets_root),
        "locale": data.get("locale", "en"),
    }


def compose(data: dict[str, Any]) -> dict[str, Any]:
    """Build optional banner image and collect facts."""

    banner_path = data.get("banner_asset")
    theme = data["theme"]
    brief = data.get("brief", "")
    image: Image.Image
    if banner_path and Path(banner_path).exists():
        image = Image.open(banner_path)
    else:
        image = Image.new("RGB", (1200, 630), color="white")
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        bbox = font.getbbox(theme)
        x = (image.width - (bbox[2] - bbox[0])) // 2
        y = (image.height - (bbox[3] - bbox[1])) // 2
        draw.text((x, y), theme, fill="black", font=font)
    image_bytes = save_image(image, fmt="WEBP")
    facts = {"theme": theme}
    if brief:
        facts["brief"] = brief
    return {**data, "image": image_bytes, "image_format": "WEBP", "facts": facts}


def write(data: dict[str, Any]) -> dict[str, Any]:
    """Generate TL;DR, sections and actions using writer pipeline."""

    locale = data.get("locale", "en")
    theme = data["facts"]["theme"]
    brief = data["facts"].get("brief", "")
    summary = f"{theme}: {brief}" if brief else theme
    sections = [
        {
            "title": get_section_title(PLUGIN_ID, "theme", locale),
            "body_md": theme,
        }
    ]
    if brief:
        sections.append(
            {
                "title": get_section_title(PLUGIN_ID, "brief", locale),
                "body_md": brief,
            }
        )
    actions = get_actions(PLUGIN_ID, locale)
    facts = {
        **data["facts"],
        "summary": summary,
        "sections": sections,
        "actions": actions,
    }
    verifier = Verifier()
    result = verifier.ensure_verified(compose_answer, facts, locale)
    result["facts"] = data["facts"]
    return result


def verify(data: dict[str, Any]) -> bool:
    """Verify generated markdown against initial facts."""

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
