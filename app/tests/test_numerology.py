from pathlib import Path
from typing import Any

from app.experts.numerology import compose, prepare, verify, write


def _run_case(full_name: str, locale: str, expected: dict[str, Any]) -> None:
    data = prepare(
        {
            "full_name": full_name,
            "birth_date": "1990-12-25",
            "target_date": "2023-09-17",
            "locale": locale,
        }
    )
    nums = data["numbers"]
    for key, value in expected.items():
        assert nums[key] == value
    composed = compose(data)
    assert composed["image"], "image should be generated"
    written = write(composed)
    assert verify(written)


def test_numerology_en(tmp_path: Path) -> None:
    _run_case(
        "John Doe",
        "en",
        {
            "life_path": 11,
            "expression": 8,
            "soul_urge": 8,
            "personality": 9,
            "birthday": 7,
            "maturity": 1,
            "growth_number": 2,
            "essence": 3,
            "transit_letters": "H D",
            "personal_year": 8,
            "personal_month": 8,
            "personal_day": 7,
            "pinnacles": [1, 8, 9, 4],
            "challenges": [4, 6, 2, 2],
        },
    )


def test_numerology_ru(tmp_path: Path) -> None:
    _run_case(
        "Иван Иванов",
        "ru",
        {
            "life_path": 11,
            "expression": 5,
            "soul_urge": 11,
            "personality": 3,
            "birthday": 7,
            "maturity": 7,
            "growth_number": 11,
            "essence": 4,
            "transit_letters": "Н О",
            "personal_year": 8,
            "personal_month": 8,
            "personal_day": 7,
            "pinnacles": [1, 8, 9, 4],
            "challenges": [4, 6, 2, 2],
        },
    )
