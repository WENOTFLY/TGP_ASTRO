from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class Diff:
    path: str
    expected: str
    found: str


@dataclass
class VerificationResult:
    ok: bool
    diffs: List[Diff]


class Verifier:
    """Simple fact verifier for generated markdown."""

    def verify(self, facts: Dict[str, Any], markdown: str) -> VerificationResult:
        diffs: List[Diff] = []
        for key, value in facts.items():
            value_str = str(value)
            if value_str not in markdown:
                diffs.append(Diff(path=key, expected=value_str, found=""))
        return VerificationResult(ok=not diffs, diffs=diffs)

    def ensure_verified(
        self,
        generate: Callable[[Dict[str, Any], str], Dict[str, Any]],
        facts: Dict[str, Any],
        locale: str,
        *,
        max_attempts: int = 2,
    ) -> Dict[str, Any]:
        attempt = 0
        while attempt < max_attempts:
            output = generate(facts, locale)
            markdown = "\n".join(section["body_md"] for section in output["sections"])
            if self.verify(facts, markdown).ok:
                return output
            attempt += 1
        return output
