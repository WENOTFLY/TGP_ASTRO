from __future__ import annotations

from datetime import date

from app.core.draw import draw_unique


def test_deterministic_draw_and_nonce() -> None:
    deck = [f"card{i}" for i in range(10)]

    first = draw_unique(
        deck,
        3,
        user_id=42,
        expert="tarot",
        spread_id="tarot_three_ppf",
        draw_date=date(2024, 1, 1),
        allow_reversed=True,
        nonce=0,
    )
    second = draw_unique(
        deck,
        3,
        user_id=42,
        expert="tarot",
        spread_id="tarot_three_ppf",
        draw_date=date(2024, 1, 1),
        allow_reversed=True,
        nonce=0,
    )
    assert first == second
    assert len({item.key for item in first}) == 3

    third = draw_unique(
        deck,
        3,
        user_id=42,
        expert="tarot",
        spread_id="tarot_three_ppf",
        draw_date=date(2024, 1, 1),
        allow_reversed=True,
        nonce=1,
    )
    assert third != first
    assert len({item.key for item in third}) == 3
    fourth = draw_unique(
        deck,
        3,
        user_id=42,
        expert="tarot",
        spread_id="tarot_three_ppf",
        draw_date=date(2024, 1, 1),
        allow_reversed=True,
        nonce=1,
    )
    assert third == fourth

    without_rev = draw_unique(
        deck,
        3,
        user_id=42,
        expert="tarot",
        spread_id="tarot_three_ppf",
        draw_date=date(2024, 1, 1),
        allow_reversed=False,
        nonce=0,
    )
    assert all(not item.reversed for item in without_rev)
