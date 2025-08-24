from datetime import date

from app.experts.numerology import prepare, compose, write, verify


def test_numerology_calculations(tmp_path):
    data = prepare(
        {
            "full_name": "John Doe",
            "birth_date": "1990-12-25",
            "target_date": "2023-09-17",
            "locale": "en",
        }
    )
    nums = data["numbers"]
    assert nums["life_path"] == 11
    assert nums["expression"] == 8
    assert nums["soul_urge"] == 8
    assert nums["personality"] == 9
    assert nums["birthday"] == 7
    assert nums["maturity"] == 1
    assert nums["personal_year"] == 8
    assert nums["personal_month"] == 8
    assert nums["personal_day"] == 7
    assert nums["pinnacles"] == [1, 8, 9, 4]
    assert nums["challenges"] == [4, 6, 2, 2]
    assert nums["matrix"] == {1: "11", 2: "22", 3: "", 4: "", 5: "5", 6: "", 7: "", 8: "", 9: "99"}

    composed = compose(data)
    assert composed["image"], "image should be generated"

    written = write(composed)
    assert written["tldr"].startswith("Life Path")
    assert verify(written)
