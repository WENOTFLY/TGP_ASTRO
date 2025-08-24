from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image, ImageDraw, ImageFont

from app.core.compose import save_image
from app.core.plugins import Plugin
from app.experts.messages import get_actions, get_cta
from app.nlp.verifier import Verifier
from app.nlp.writer import compose_answer

PLUGIN_ID = "numerology"
ASSETS_ROOT = Path("assets/numerology")
_ALPHABET_CACHE: Dict[str, Dict[str, int]] = {}
_RULES: Dict[str, Any] | None = None


def _load_rules() -> Dict[str, Any]:
    global _RULES
    if _RULES is None:
        path = ASSETS_ROOT / "rules.json"
        _RULES = json.loads(path.read_text(encoding="utf-8"))
    return _RULES


def _load_alphabet(locale: str) -> Dict[str, int]:
    if locale not in _ALPHABET_CACHE:
        path = ASSETS_ROOT / "alphabets" / f"{locale}.json"
        _ALPHABET_CACHE[locale] = json.loads(path.read_text(encoding="utf-8"))
    return _ALPHABET_CACHE[locale]


VOWELS: Dict[str, set[str]] = {
    "en": set("AEIOUY"),
    "ru": set("АЕЁИОУЫЭЮЯ"),
}


def _reduce(n: int) -> int:
    masters = set(_load_rules().get("master_numbers", []))
    while n not in masters and n >= 10:
        n = sum(int(d) for d in str(n))
    return n


def _letters_value(
    name: str,
    alphabet: Dict[str, int],
    locale: str,
    *,
    vowels: bool = False,
    consonants: bool = False,
) -> int:
    vowels_set = VOWELS.get(locale, VOWELS["en"])
    total = 0
    for ch in name.upper():
        if not ch.isalpha():
            continue
        if ch not in alphabet:
            raise ValueError(f"Unsupported character: {ch}")
        if vowels and ch not in vowels_set:
            continue
        if consonants and ch in vowels_set:
            continue
        total += alphabet[ch]
    return _reduce(total)


def _calc_matrix(birth: date) -> Dict[int, str]:
    digits = [d for d in birth.strftime("%d%m%Y") if d.isdigit()]
    matrix = {i: "" for i in range(1, 10)}
    for d in digits:
        if d == "0":
            continue
        matrix[int(d)] += d
    return matrix


def _calc_pinnacles(birth: date) -> List[int]:
    m = _reduce(birth.month)
    d = _reduce(birth.day)
    y = _reduce(sum(int(ch) for ch in str(birth.year)))
    p1 = _reduce(m + d)
    p2 = _reduce(d + y)
    p3 = _reduce(p1 + p2)
    p4 = _reduce(m + y)
    return [p1, p2, p3, p4]


def _calc_challenges(birth: date) -> List[int]:
    m = _reduce(birth.month)
    d = _reduce(birth.day)
    y = _reduce(sum(int(ch) for ch in str(birth.year)))
    c1 = _reduce(abs(m - d))
    c2 = _reduce(abs(d - y))
    c3 = _reduce(abs(c1 - c2))
    c4 = _reduce(abs(m - y))
    return [c1, c2, c3, c4]


def _calc_transits(
    name: str, birth: date, target: date, alphabet: Dict[str, int]
) -> tuple[list[str], int]:
    age = target.year - birth.year
    if (target.month, target.day) < (birth.month, birth.day):
        age -= 1
    parts = [p for p in name.strip().split() if p]
    letters: list[str] = []
    total = 0
    for part in parts:
        seq = [ch for ch in part.upper() if ch.isalpha()]
        if not seq:
            continue
        remaining = age
        idx = 0
        while True:
            ch = seq[idx % len(seq)]
            duration = alphabet[ch]
            if remaining < duration:
                letters.append(ch)
                total += alphabet[ch]
                break
            remaining -= duration
            idx += 1
    essence = _reduce(total) if letters else 0
    return letters, essence


def _calc_numbers(name: str, birth: date, target: date, locale: str) -> Dict[str, Any]:
    alphabet = _load_alphabet(locale)
    life_path = _reduce(sum(int(d) for d in birth.strftime("%Y%m%d") if d.isdigit()))
    expression = _letters_value(name, alphabet, locale)
    soul = _letters_value(name, alphabet, locale, vowels=True)
    personality = _letters_value(name, alphabet, locale, consonants=True)
    birthday = _reduce(birth.day)
    maturity = _reduce(life_path + expression)

    first = name.split()[0] if name.split() else ""
    growth_number = _letters_value(first, alphabet, locale) if first else 0
    transit_letters, essence = _calc_transits(name, birth, target, alphabet)
    transit_str = " ".join(transit_letters)

    year_sum = _reduce(target.year)
    personal_year = _reduce(_reduce(birth.month) + _reduce(birth.day) + year_sum)
    personal_month = _reduce(personal_year + _reduce(target.month))
    personal_day = _reduce(personal_month + _reduce(target.day))

    pinnacles = _calc_pinnacles(birth)
    challenges = _calc_challenges(birth)
    matrix = _calc_matrix(birth)

    return {
        "life_path": life_path,
        "expression": expression,
        "soul_urge": soul,
        "personality": personality,
        "birthday": birthday,
        "maturity": maturity,
        "growth_number": growth_number,
        "essence": essence,
        "transit_letters": transit_str,
        "personal_year": personal_year,
        "personal_month": personal_month,
        "personal_day": personal_day,
        "pinnacles": pinnacles,
        "challenges": challenges,
        "matrix": matrix,
    }


@dataclass
class Period:
    label: str
    pinnacle: int
    challenge: int
    start: int
    end: int | None


def form_steps(locale: str) -> list[dict[str, Any]]:
    return [
        {"id": "full_name", "type": "string"},
        {"id": "birth_date", "type": "date"},
        {"id": "target_date", "type": "date"},
    ]


def prepare(data: dict[str, Any]) -> dict[str, Any]:
    full_name = data["full_name"].strip()
    birth_raw = data["birth_date"]
    target_raw = data.get("target_date")
    if isinstance(birth_raw, str):
        birth = date.fromisoformat(birth_raw)
    else:
        birth = birth_raw
    if isinstance(target_raw, str):
        target = date.fromisoformat(target_raw)
    elif target_raw is None:
        target = date.today()
    else:
        target = target_raw
    locale = data.get("locale", "en")
    numbers = _calc_numbers(full_name, birth, target, locale)
    periods: List[Period] = []
    ages = [(0, 27), (28, 36), (37, 45), (46, None)]
    for i, (p, c) in enumerate(
        zip(numbers["pinnacles"], numbers["challenges"], strict=True), start=1
    ):
        start, end = ages[i - 1]
        periods.append(Period(f"{i}", p, c, start, end))
    return {
        "full_name": full_name,
        "birth_date": birth,
        "target_date": target,
        "locale": locale,
        "numbers": numbers,
        "periods": periods,
        "matrix": numbers["matrix"],
    }


def compose(data: dict[str, Any]) -> dict[str, Any]:
    matrix: Dict[int, str] = data["matrix"]
    periods: List[Period] = data["periods"]
    cell = 60
    spacing = 5
    width = cell * 3 + spacing * 2
    matrix_h = cell * 3 + spacing * 2
    height = matrix_h + 80
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    order = [1, 4, 7, 2, 5, 8, 3, 6, 9]
    for idx, num in enumerate(order):
        row, col = divmod(idx, 3)
        x = col * (cell + spacing)
        y = row * (cell + spacing)
        draw.rectangle([x, y, x + cell, y + cell], outline="black")
        text = matrix[num]
        bbox = font.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            (x + cell / 2 - tw / 2, y + cell / 2 - th / 2),
            text,
            fill="black",
            font=font,
        )
    y = matrix_h + 5
    for p in periods:
        end = p.end if p.end is not None else "+"
        text = f"P{p.label}:{p.pinnacle} C{p.label}:{p.challenge} {p.start}-{end}"
        draw.text((5, y), text, fill="black", font=font)
        y += 15
    image_bytes = save_image(img, fmt="WEBP")
    return {
        **data,
        "image": image_bytes,
        "image_format": "WEBP",
        "facts": data["numbers"],
    }


def write(data: dict[str, Any]) -> dict[str, Any]:
    locale = data.get("locale", "en")
    nums = data["numbers"]
    sections: List[Dict[str, str]] = []
    core_keys = [
        "life_path",
        "expression",
        "soul_urge",
        "personality",
        "birthday",
        "maturity",
        "growth_number",
        "essence",
        "transit_letters",
        "personal_year",
        "personal_month",
        "personal_day",
    ]
    for key in core_keys:
        title = key.replace("_", " ").title()
        sections.append({"title": title, "body_md": f"{title}: {nums[key]}"})
    for i, val in enumerate(nums["pinnacles"], start=1):
        sections.append({"title": f"Pinnacle {i}", "body_md": f"Pinnacle {i}: {val}"})
    for i, val in enumerate(nums["challenges"], start=1):
        sections.append({"title": f"Challenge {i}", "body_md": f"Challenge {i}: {val}"})
    summary = f"Life Path {nums['life_path']}, Expression {nums['expression']}"
    actions = get_actions(PLUGIN_ID, locale)
    facts: Dict[str, Any] = {k: nums[k] for k in core_keys}
    for i, v in enumerate(nums["pinnacles"], start=1):
        facts[f"pinnacle_{i}"] = v
    for i, v in enumerate(nums["challenges"], start=1):
        facts[f"challenge_{i}"] = v
    verify_facts = {
        **facts,
        "summary": summary,
        "sections": sections,
        "actions": actions,
    }
    verifier = Verifier()
    output = verifier.ensure_verified(compose_answer, verify_facts, locale)
    result: Dict[str, Any] = output
    result["facts"] = facts
    return result


def verify(data: dict[str, Any]) -> bool:
    facts = data.get("facts", {})
    markdown = "\n".join(section["body_md"] for section in data.get("sections", []))
    return Verifier().verify(facts, markdown).ok


def cta(locale: str) -> list[str]:
    return get_cta(PLUGIN_ID, locale)


plugin = Plugin(
    plugin_id=PLUGIN_ID,
    form_steps=form_steps,
    prepare=prepare,
    compose=compose,
    write=write,
    verify=verify,
    cost=0,
    cta=cta,
    products_supported=("basic",),
)
