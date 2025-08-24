from pathlib import Path

from app.experts.numerology import compose, prepare, verify, write


def _run_case(
    full_name: str, locale: str, expression: int, soul: int, personality: int
) -> None:
    data = prepare(
        {
            "full_name": full_name,
            "birth_date": "1990-12-25",
            "target_date": "2023-09-17",
            "locale": locale,
        }
    )
    nums = data["numbers"]
    assert nums["expression"] == expression
    assert nums["soul_urge"] == soul
    assert nums["personality"] == personality
    composed = compose(data)
    assert composed["image"], "image should be generated"
    written = write(composed)
    assert verify(written)


def test_numerology_en(tmp_path: Path) -> None:
    _run_case("John Doe", "en", 8, 8, 9)


def test_numerology_ru(tmp_path: Path) -> None:
    _run_case("Иван Иванов", "ru", 5, 11, 3)
