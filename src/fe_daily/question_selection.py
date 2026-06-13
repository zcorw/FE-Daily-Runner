import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FocusTarget:
    label: str
    count: int


FOCUS_PART_PATTERN = re.compile(r"^(?P<label>.+?)\s+(?P<count>\d+)$")


def parse_practice_focus(practice_focus: str) -> list[FocusTarget]:
    text = practice_focus.strip()
    if not text:
        raise ValueError("practice focus must not be blank")

    parts = [part.strip() for part in text.split(",") if part.strip()]
    targets: list[FocusTarget] = []

    for part in parts:
        match = FOCUS_PART_PATTERN.match(part)
        if match is None:
            if len(parts) == 1:
                return [FocusTarget(label=part, count=10)]
            raise ValueError(f"practice focus item is missing a count: {part}")
        targets.append(
            FocusTarget(
                label=match.group("label").strip(),
                count=int(match.group("count")),
            )
        )

    return targets


def build_candidate_search_payloads(targets: list[FocusTarget]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for target in targets:
        if target.count <= 0:
            raise ValueError("focus target count must be positive")
        if not target.label.strip():
            raise ValueError("focus target label must not be blank")
        payloads.append(
            {
                "keywords": [target.label],
                "examPart": "科目A",
                "limit": target.count,
            }
        )
    return payloads
