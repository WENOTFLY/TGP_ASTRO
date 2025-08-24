from typing import Any

from app.nlp.guide import get_tip
from app.nlp.localizer import (
    get_disclaimers,
    get_expert_name,
    get_ui_string,
)
from app.nlp.verifier import Verifier
from app.nlp.writer import compose_answer


def test_guide_tip() -> None:
    tip = get_tip("tarot", "intro", "en")
    assert tip == {"tip": "Focus on your question for the cards."}


def test_writer_compose_answer() -> None:
    facts = {
        "summary": "Short summary",
        "details": "Detailed text",
        "actions": ["a1", "a2", "a3"],
    }
    result = compose_answer(facts, "en")
    assert result["tldr"] == "Short summary"
    assert result["sections"][0]["body_md"] == "Detailed text"
    assert len(result["actions"]) == 3
    assert "For entertainment purposes only." in result["disclaimers"][0]


def test_verifier_regenerates() -> None:
    facts = {"number": 42}
    calls: list[int] = []

    def generate(facts: dict[str, int], locale: str) -> dict[str, Any]:
        calls.append(len(calls))
        if len(calls) == 1:
            return {
                "tldr": "",
                "sections": [{"title": "", "body_md": "wrong"}],
                "actions": [],
                "disclaimers": [],
            }
        return {
            "tldr": "",
            "sections": [{"title": "", "body_md": "the answer is 42"}],
            "actions": [],
            "disclaimers": [],
        }

    verifier = Verifier()
    output = verifier.ensure_verified(generate, facts, "en")
    assert output["sections"][0]["body_md"] == "the answer is 42"
    assert len(calls) == 2


def test_localizer() -> None:
    assert get_ui_string("welcome", "ru") == "Добро пожаловать"
    assert get_expert_name("tarot", "en") == "Tarot reader"
    assert get_disclaimers("ru")[0].startswith("Информация")
