from app.experts import astrology


def test_astrology_positions() -> None:
    params = {
        "birth_date": "2000-01-01",
        "birth_time": "12:00",
        "lat": 0.0,
        "lon": 0.0,
        "locale": "en",
    }
    prep = astrology.prepare(params)
    comp = astrology.compose(prep)
    sun = next(item for item in comp["table"] if item["planet"] == "Sun")
    assert sun["sign"] == "Capricorn"
    text = astrology.write(comp)
    assert astrology.verify(text)


def test_astrology_solar_disclaimer() -> None:
    params = {
        "birth_date": "2000-01-01",
        "lat": 0.0,
        "lon": 0.0,
        "locale": "en",
    }
    prep = astrology.prepare(params)
    comp = astrology.compose(prep)
    text = astrology.write(comp)
    assert any("time" in d.lower() for d in text["disclaimers"])
