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
from app.experts import runes


def _create_image(path: Path, size: tuple[int, int] = (300, 300)) -> None:
    Image.new("RGB", size, "white").save(path)


def _setup_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    models.JSONB = SQLITE_JSON  # type: ignore[attr-defined]
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()


def test_runes_pipeline(tmp_path: Path) -> None:
    ASSET_CACHE.clear()
    set_dir = tmp_path / "runes" / "testdeck"
    runes_dir = set_dir / "runes"
    runes_dir.mkdir(parents=True)
    _create_image(set_dir / "back.png")
    for i in range(5):
        _create_image(runes_dir / f"{i}.png")
    manifest = {
        "set_id": "testdeck",
        "name": {"en": "Sample", "ru": "Пример"},
        "type": "runes",
        "image": {
            "aspect_ratio": "1:1",
            "allow_reversed": True,
            "default_back": "back.png",
        },
        "runes": [
            {
                "key": f"r{i}",
                "display": {"en": f"Rune {i}"},
                "file": f"{i}.png",
                "can_reverse": i % 2 == 0,
            }
            for i in range(5)
        ],
    }
    (set_dir / "set.json").write_text(json.dumps(manifest), encoding="utf-8")
    session = _setup_session()
    load_assets(tmp_path, session)

    params = {
        "set_id": "testdeck",
        "spread_id": "runes_five_cross",
        "user_id": 42,
        "draw_date": date(2024, 1, 1),
        "nonce": 0,
        "locale": "en",
        "assets_root": str(tmp_path),
    }
    prep1 = runes.prepare(params)
    prep2 = runes.prepare(params)
    assert prep1["runes"] == prep2["runes"]

    conf = ASSET_CACHE["testdeck"]["config"]
    by_key = {r["key"]: r for r in conf["runes"]}
    assert any(r["reversed"] for r in prep1["runes"])
    for r in prep1["runes"]:
        if not by_key[r["key"]]["can_reverse"]:
            assert not r["reversed"]

    comp = runes.compose(prep1)
    assert isinstance(comp["image"], bytes) and len(comp["image"]) > 0

    text = runes.write(comp)
    assert text["tldr"]
    assert text["sections"]
    assert text["actions"]
    assert text["disclaimers"]
    assert runes.verify(text)
