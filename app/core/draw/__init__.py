from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import date
from typing import List, Sequence


@dataclass(frozen=True)
class DrawItem:
    """Result of a draw: item key and orientation."""

    key: str
    reversed: bool = False


def generate_seed(
    user_id: int | str,
    expert: str,
    spread_id: str,
    draw_date: date,
    nonce: int = 0,
) -> int:
    """Compute deterministic seed for draws.

    The seed formula follows Appendix B:
    SHA256("user_id|expert|spread_id|YYYYMMDD|nonce").
    """

    base = f"{user_id}|{expert}|{spread_id}|{draw_date:%Y%m%d}|{nonce}"
    return int(hashlib.sha256(base.encode("utf-8")).hexdigest(), 16)


def draw_unique(
    items: Sequence[str],
    count: int,
    *,
    user_id: int | str,
    expert: str,
    spread_id: str,
    draw_date: date,
    nonce: int = 0,
    allow_reversed: bool = False,
    p_reversed: float = 0.5,
) -> List[DrawItem]:
    """Draw unique items deterministically.

    Args:
        items: Pool of item keys to draw from.
        count: Number of items to draw; must not exceed population size.
        user_id, expert, spread_id, draw_date, nonce: parameters for seed generation.
        allow_reversed: Whether orientation may be reversed.
        p_reversed: Probability of an item being reversed when allowed.

    Returns:
        List of DrawItem preserving draw order.
    """

    if count > len(items):
        raise ValueError("Not enough unique items to draw")
    seed = generate_seed(user_id, expert, spread_id, draw_date, nonce)
    rng = random.Random(seed)
    selection = rng.sample(list(items), count)
    result: List[DrawItem] = []
    for key in selection:
        is_reversed = allow_reversed and rng.random() < p_reversed
        result.append(DrawItem(key=key, reversed=is_reversed))
    return result


__all__ = ["DrawItem", "draw_unique", "generate_seed"]
