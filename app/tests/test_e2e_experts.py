import json
import shutil
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Session, sessionmaker

from app.core.assets import ASSET_CACHE, load_assets
import app.core.limits as limits
from app.db import models
from app.db.base import Base
from app.experts import (
    assistant,
    astrology,
    copywriter,
    dreams,
    lenormand,
    numerology,
    runes,
    tarot,
)


def _create_image(path: Path, size: tuple[int, int] = (200, 300)) -> None:
    Image.new("RGB", size, "white").save(path)


@pytest.fixture(scope="module")
def session_and_assets(tmp_path_factory: pytest.TempPathFactory) -> tuple[Session, Path]:
    tmp_assets = tmp_path_factory.mktemp("assets")

    # Tarot deck
    tarot_dir = tmp_assets / "tarot" / "tarot_sample"
    tarot_cards = tarot_dir / "cards"
    tarot_cards.mkdir(parents=True)
    _create_image(tarot_dir / "back.png", size=(300, 500))
    for i in range(3):
        _create_image(tarot_cards / f"{i}.png", size=(300, 500))
    tarot_manifest = {
        "deck_id": "tarot_sample",
        "name": {"en": "Sample"},
        "type": "tarot",
        "image": {"aspect_ratio": "3:5", "allow_reversed": True, "default_back": "back.png"},
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
    (tarot_dir / "deck.json").write_text(json.dumps(tarot_manifest), encoding="utf-8")

    # Lenormand deck
    leno_dir = tmp_assets / "lenormand" / "leno_sample"
    leno_cards = leno_dir / "cards"
    leno_cards.mkdir(parents=True)
    _create_image(leno_dir / "back.png", size=(300, 500))
    for i in range(3):
        _create_image(leno_cards / f"{i}.png", size=(300, 500))
    leno_manifest = {
        "deck_id": "leno_sample",
        "name": {"en": "Sample"},
        "type": "lenormand",
        "image": {"aspect_ratio": "3:5", "default_back": "back.png"},
        "cards": [
            {
                "key": f"l{i}",
                "display": {"en": f"Card {i}"},
                "file": f"{i}.png",
            }
            for i in range(3)
        ],
    }
    (leno_dir / "deck.json").write_text(json.dumps(leno_manifest), encoding="utf-8")

    # Runes set
    runes_dir = tmp_assets / "runes" / "runes_sample"
    runes_items = runes_dir / "runes"
    runes_items.mkdir(parents=True)
    _create_image(runes_dir / "back.png", size=(200, 200))
    for i in range(3):
        _create_image(runes_items / f"{i}.png", size=(200, 200))
    runes_manifest = {
        "set_id": "runes_sample",
        "name": {"en": "Sample"},
        "type": "runes",
        "image": {"aspect_ratio": "1:1", "allow_reversed": True, "default_back": "back.png"},
        "runes": [
            {
                "key": f"r{i}",
                "display": {"en": f"Rune {i}"},
                "file": f"{i}.png",
                "can_reverse": True,
            }
            for i in range(3)
        ],
    }
    (runes_dir / "set.json").write_text(json.dumps(runes_manifest), encoding="utf-8")

    engine = create_engine("sqlite:///:memory:", future=True)
    models.JSONB = SQLITE_JSON  # type: ignore[attr-defined]
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()
    entitlement = models.Entitlement(
        id=1,
        user_id=1,
        product="basic",
        status="active",
        quota_total=100,
        quota_left=100,
    )
    session.add(entitlement)
    session.commit()

    ASSET_CACHE.clear()
    load_assets(tmp_assets, session)
    # Copy extra assets not handled by loader
    shutil.copytree(Path("assets/numerology"), tmp_assets / "numerology")
    shutil.copytree(Path("assets/dreams"), tmp_assets / "dreams")
    return session, tmp_assets


EXPERT_CASES = [
    (tarot.plugin, {"deck_id": "tarot_sample", "spread_id": "tarot_three_ppf", "question": "Q"}),
    (lenormand.plugin, {"deck_id": "leno_sample", "spread_id": "leno_three_line", "question": "Q"}),
    (runes.plugin, {"set_id": "runes_sample", "spread_id": "runes_one", "question": "Q"}),
    (
        numerology.plugin,
        {"full_name": "John Doe", "birth_date": "2000-01-02", "target_date": "2024-01-01"},
    ),
    (
        astrology.plugin,
        {"birth_date": "2000-01-01", "birth_time": "12:00", "lat": 0.0, "lon": 0.0},
    ),
    (dreams.plugin, {"dream": "I saw a cat and water"}),
    (copywriter.plugin, {"theme": "Marketing", "brief": "Ad text"}),
    (assistant.plugin, {"theme": "Travel", "brief": "Europe"}),
]


@pytest.mark.parametrize("plugin,data", EXPERT_CASES)
def test_expert_flow(plugin, data, session_and_assets):
    session, assets_root = session_and_assets

    if plugin is numerology.plugin:
        numerology.ASSETS_ROOT = assets_root / "numerology"
        numerology._ALPHABET_CACHE.clear()
        numerology._RULES = None

    params = {**data, "user_id": 1, "locale": "en", "assets_root": str(assets_root)}

    steps = plugin.form_steps("en")
    assert steps

    prepared = plugin.prepare(params)
    composed = plugin.compose(prepared)
    text = plugin.write(composed)
    assert text["actions"]
    assert plugin.verify(text)

    old_flood = limits.ANTI_FLOOD_SECONDS
    limits.ANTI_FLOOD_SECONDS = 0
    before = session.query(models.Entitlement).filter_by(user_id=1).first().quota_left
    limits.consume(session, 1, plugin.plugin_id)
    after = session.query(models.Entitlement).filter_by(user_id=1).first().quota_left
    limits.ANTI_FLOOD_SECONDS = old_flood
    assert after == before - 1
