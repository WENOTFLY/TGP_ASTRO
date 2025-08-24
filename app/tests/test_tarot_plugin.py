from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Session, sessionmaker

from app.core.assets import ASSET_CACHE, load_assets
from app.db import models
from app.db.base import Base
from app.experts import tarot


def _create_image(path: Path, size: tuple[int, int] = (300, 500)) -> None:
    Image.new("RGB", size, "white").save(path)


def _setup_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    models.JSONB = SQLITE_JSON
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()


def test_tarot_pipeline(tmp_path: Path) -> None:
    ASSET_CACHE.clear()
    deck_dir = tmp_path / "tarot" / "sample"
    cards_dir = deck_dir / "cards"
    cards_dir.mkdir(parents=True)
    _create_image(deck_dir / "back.png")
    Image.new("RGBA", (300, 500), (0, 0, 0, 0)).save(deck_dir / "frame.png")
    for i in range(3):
        _create_image(cards_dir / f"{i}.png")
    manifest = {
        "deck_id": "sample",
        "name": {"en": "Sample", "ru": "Пример"},
        "type": "tarot",
        "image": {
            "aspect_ratio": "3:5",
            "allow_reversed": True,
            "default_back": "back.png",
        },
        "cards": [
            {
                "key": f"c{i}",
                "display": {"en": f"Card {i}"},
                "file": f"{i}.png",
                "arcana": "major",
                "upright": [],
                "reversed": [],
            }
            for i in range(3)
        ],
    }
    (deck_dir / "deck.json").write_text(json.dumps(manifest), encoding="utf-8")
    session = _setup_session()
    load_assets(tmp_path, session)

    params = {
        "deck_id": "sample",
        "spread_id": "tarot_three_ppf",
        "user_id": 42,
        "draw_date": date(2024, 1, 1),
        "nonce": 0,
        "locale": "en",
        "assets_root": str(tmp_path),
    }
    prep1 = tarot.prepare(params)
    prep2 = tarot.prepare(params)
    assert prep1["cards"] == prep2["cards"]

    comp = tarot.compose(prep1)
    assert isinstance(comp["image"], bytes) and len(comp["image"]) > 0

    text = tarot.write(comp)
    assert text["tldr"]
    assert len(text["actions"]) == 3
    assert text["disclaimers"]
    assert tarot.verify(text)
