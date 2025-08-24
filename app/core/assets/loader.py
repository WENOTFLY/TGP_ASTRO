from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image
from sqlalchemy.orm import Session

from app.db.models import Deck


class AssetValidationError(Exception):
    """Raised when asset validation fails."""


def _check_image(path: Path, ratio: float) -> None:
    with Image.open(path) as img:
        width, height = img.size
    if width <= 0 or height <= 0:
        raise AssetValidationError(f"Invalid image size: {path}")
    if abs((width / height) - ratio) > 0.01:
        raise AssetValidationError(
            "Bad aspect ratio for " f"{path}: {width}x{height} expected {ratio:.2f}"
        )


def _make_thumb(src: Path, dest: Path, size: tuple[int, int]) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img.thumbnail(size)
        img.save(dest)


ASSET_CACHE: dict[str, dict[str, Any]] = {}


def load_assets(
    root: Path,
    session: Session,
    *,
    thumb_size: tuple[int, int] = (256, 256),
) -> None:
    """Validate assets and populate deck index in DB and memory cache."""

    for deck_type_dir in root.iterdir():
        if not deck_type_dir.is_dir():
            continue
        deck_type = deck_type_dir.name
        for deck_dir in deck_type_dir.iterdir():
            if not deck_dir.is_dir():
                continue
            manifest_path = deck_dir / "deck.json"
            id_key = "deck_id"
            if not manifest_path.exists():
                manifest_path = deck_dir / "set.json"
                id_key = "set_id"
            if not manifest_path.exists():
                raise AssetValidationError(f"Missing manifest in {deck_dir}")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if id_key not in manifest:
                raise AssetValidationError(f"Missing {id_key} in {manifest_path}")
            deck_id = manifest[id_key]
            if manifest.get("type") != deck_type:
                raise AssetValidationError(
                    "Type mismatch for "
                    f"{deck_id}: {manifest.get('type')} != {deck_type}"
                )
            name = manifest.get("name")
            if not isinstance(name, dict) or not name:
                raise AssetValidationError(f"Missing name in {manifest_path}")
            image_conf = manifest.get("image", {})
            aspect = image_conf.get("aspect_ratio")
            if aspect is None:
                raise AssetValidationError(
                    f"Missing image.aspect_ratio in {manifest_path}"
                )
            ar_w, ar_h = [int(x) for x in str(aspect).split(":")]
            ratio = ar_w / ar_h
            back_path = deck_dir / image_conf.get("default_back", "back.png")
            if not back_path.exists():
                raise AssetValidationError(f"Missing back image for {deck_id}")
            _check_image(back_path, ratio)
            items_key = "cards" if "cards" in manifest else "runes"
            items = manifest.get(items_key)
            if not isinstance(items, list) or not items:
                raise AssetValidationError(f"No {items_key} in {manifest_path}")
            items_dir = deck_dir / items_key
            for item in items:
                for key in ("key", "display", "file"):
                    if key not in item:
                        raise AssetValidationError(
                            f"Missing '{key}' for item in {manifest_path}"
                        )
                file_name = item["file"]
                img_path = items_dir / file_name
                if not img_path.exists():
                    raise AssetValidationError(f"Missing image {img_path}")
                _check_image(img_path, ratio)
                _make_thumb(img_path, deck_dir / "thumbs" / file_name, thumb_size)
            _make_thumb(back_path, deck_dir / "thumbs" / back_path.name, thumb_size)
            deck_row = Deck(type=deck_type, name_json=name, config_json=manifest)
            session.add(deck_row)
            session.commit()
            ASSET_CACHE[deck_id] = {
                "db_id": deck_row.id,
                "type": deck_type,
                "name": name,
                "config": manifest,
            }
