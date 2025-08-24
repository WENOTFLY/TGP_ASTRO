from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
from math import radians
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import swisseph as swe

from app.core.plugins import Plugin
from app.nlp.verifier import Verifier
from app.nlp.writer import compose_answer

PLUGIN_ID = "astrology"

PLANETS: Dict[str, int] = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}

SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

ASPECT_ANGLES = {
    "Conjunction": 0,
    "Sextile": 60,
    "Square": 90,
    "Trine": 120,
    "Opposition": 180,
}

ORB = 6.0


def form_steps(locale: str) -> list[dict[str, Any]]:
    return [
        {"id": "birth_date", "type": "string"},
        {"id": "birth_time", "type": "string", "required": False},
        {"id": "lat", "type": "number"},
        {"id": "lon", "type": "number"},
    ]


def _parse_datetime(data: dict[str, Any]) -> tuple[datetime, bool]:
    d = date.fromisoformat(str(data["birth_date"]))
    time_str = data.get("birth_time")
    if time_str:
        t = datetime.strptime(time_str, "%H:%M").time()
        dt = datetime.combine(d, t)
        solar = False
    else:
        dt = datetime.combine(d, datetime.min.time()).replace(hour=12, minute=0)
        solar = True
    return dt, solar


def prepare(data: dict[str, Any]) -> dict[str, Any]:
    dt, solar = _parse_datetime(data)
    lat = float(data.get("lat", 0))
    lon = float(data.get("lon", 0))
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60)

    positions: Dict[str, float] = {}
    for name, body in PLANETS.items():
        pos, _ = swe.calc_ut(jd, body)
        positions[name] = pos[0]

    houses: List[float] | None = None
    if not solar:
        houses, _ = swe.houses(jd, lat, lon)

    aspects: List[tuple[str, str, str, float]] = []
    planet_items = list(positions.items())
    for i, (p1, lon1) in enumerate(planet_items):
        for p2, lon2 in planet_items[i + 1 :]:
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff
            for name, angle in ASPECT_ANGLES.items():
                if abs(diff - angle) <= ORB:
                    orb = round(diff - angle, 2)
                    aspects.append((p1, p2, name, orb))

    return {
        "jd": jd,
        "positions": positions,
        "houses": houses,
        "aspects": aspects,
        "solar": solar,
        "lat": lat,
        "lon": lon,
        "locale": data.get("locale", "en"),
    }


@dataclass
class TableEntry:
    planet: str
    sign: str
    degree: float


def _build_table(positions: Dict[str, float]) -> list[TableEntry]:
    table: List[TableEntry] = []
    for planet, lon in positions.items():
        sign_idx = int(lon // 30) % 12
        deg = lon % 30
        table.append(TableEntry(planet, SIGNS[sign_idx], round(deg, 2)))
    return table


def compose(data: dict[str, Any]) -> dict[str, Any]:
    positions = data["positions"]
    houses = data.get("houses")

    fig = plt.figure(figsize=(4, 4))
    ax: Any = fig.add_subplot(111, polar=True)
    ax.set_theta_direction(-1)
    ax.set_theta_offset(radians(90))
    ax.set_xticks([radians(i) for i in range(0, 360, 30)])
    ax.set_yticks([])

    if houses:
        for cusp in houses:
            ax.plot(
                [radians(cusp), radians(cusp)],
                [0, 1],
                color="black",
                linewidth=0.5,
            )

    for planet, lon in positions.items():
        ax.scatter(radians(lon), 0.9, s=20)
        ax.text(radians(lon), 0.95, planet[:2], ha="center", va="center", fontsize=8)

    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    image_bytes = buf.getvalue()

    table = _build_table(positions)
    facts = {e.planet: f"{e.sign} {e.degree:.2f}°" for e in table}

    return {
        **data,
        "image": image_bytes,
        "image_format": "PNG",
        "table": [e.__dict__ for e in table],
        "facts": facts,
    }


def write(data: dict[str, Any]) -> dict[str, Any]:
    locale = data.get("locale", "en")
    table = [TableEntry(**t) for t in data["table"]]
    solar = bool(data.get("solar"))

    sun = next(e for e in table if e.planet == "Sun")
    moon = next(e for e in table if e.planet == "Moon")
    summary = f"Sun in {sun.sign}, Moon in {moon.sign}"
    details = "\n".join(f"{e.planet}: {e.sign} {e.degree:.2f}°" for e in table)
    actions = [
        "Reflect on these planetary placements.",
        "Consider how aspects influence your chart.",
        "Use this insight for self-awareness.",
    ]
    disclaimers = []
    if solar:
        disclaimers.append("Birth time unknown; chart is calculated for solar noon.")

    facts = {
        **data["facts"],
        "summary": summary,
        "details": details,
        "actions": actions,
        "disclaimers": disclaimers,
    }

    verifier = Verifier()
    output = verifier.ensure_verified(compose_answer, facts, locale)
    result: dict[str, Any] = output
    result["facts"] = data["facts"]
    return result


def verify(data: dict[str, Any]) -> bool:
    facts = data.get("facts", {})
    markdown = "\n".join(section["body_md"] for section in data.get("sections", []))
    verifier = Verifier()
    result = verifier.verify(facts, markdown)
    return bool(getattr(result, "ok", False))


def cta(locale: str) -> list[str]:
    return ["Calculate again", "Share"]


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
