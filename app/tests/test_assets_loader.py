from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Session, sessionmaker

from app.core.assets import ASSET_CACHE, AssetValidationError, load_assets
from app.db import models
from app.db.base import Base
from app.db.models import Deck


def _create_image(path: Path, size: tuple[int, int] = (300, 500)) -> None:
    Image.new("RGB", size, "white").save(path)


def _setup_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    models.JSONB = SQLITE_JSON  # type: ignore[attr-defined]
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()


def test_load_assets(tmp_path: Path) -> None:
    ASSET_CACHE.clear()
    assets_root = tmp_path
    deck_dir = assets_root / "tarot" / "sample"
    cards_dir = deck_dir / "cards"
    cards_dir.mkdir(parents=True)
    _create_image(deck_dir / "back.png")
    _create_image(cards_dir / "0.png")
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
                "key": "major_0",
                "display": {"en": "Zero", "ru": "Ноль"},
                "file": "0.png",
                "arcana": "major",
                "upright": ["a"],
                "reversed": ["b"],
            }
        ],
    }
    (deck_dir / "deck.json").write_text(json.dumps(manifest), encoding="utf-8")
    session = _setup_session()
    load_assets(assets_root, session)
    decks = session.query(Deck).all()
    assert len(decks) == 1
    assert "sample" in ASSET_CACHE
    assert (deck_dir / "thumbs" / "0.png").exists()
    assert (deck_dir / "thumbs" / "back.png").exists()


def test_load_assets_bad_ratio(tmp_path: Path) -> None:
    ASSET_CACHE.clear()
    assets_root = tmp_path
    deck_dir = assets_root / "tarot" / "bad"
    cards_dir = deck_dir / "cards"
    cards_dir.mkdir(parents=True)
    _create_image(deck_dir / "back.png", size=(100, 100))
    _create_image(cards_dir / "0.png", size=(100, 100))
    manifest = {
        "deck_id": "bad",
        "name": {"en": "Bad", "ru": "Плохой"},
        "type": "tarot",
        "image": {
            "aspect_ratio": "3:5",
            "allow_reversed": True,
            "default_back": "back.png",
        },
        "cards": [
            {
                "key": "k",
                "display": {"en": "e", "ru": "r"},
                "file": "0.png",
                "arcana": "major",
                "upright": [],
                "reversed": [],
            }
        ],
    }
    (deck_dir / "deck.json").write_text(json.dumps(manifest), encoding="utf-8")
    session = _setup_session()
    with pytest.raises(AssetValidationError):
        load_assets(assets_root, session)
