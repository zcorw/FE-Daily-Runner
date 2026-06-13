import re
from dataclasses import dataclass
from typing import Any


class InsufficientQuestionsError(RuntimeError):
    pass


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


def select_subject_a_questions(
    candidate_groups: list[list[dict[str, Any]]],
    *,
    required_count: int = 10,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for group in candidate_groups:
        for question in group:
            if question.get("examPart") != "科目A":
                continue
            url = question.get("url")
            if not isinstance(url, str) or not url:
                continue
            if url in seen_urls:
                continue
            selected.append(question)
            seen_urls.add(url)
            if len(selected) == required_count:
                return selected

    raise InsufficientQuestionsError(
        f"needed {required_count} 科目A questions, found {len(selected)}"
    )
