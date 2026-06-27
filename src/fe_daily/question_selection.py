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
SUBJECT_A_EXAM_PART = "科目A"
LEGACY_MOJIBAKE_SUBJECT_A_EXAM_PART = "绉戠洰A"
SUBJECT_A_EXAM_PARTS = {SUBJECT_A_EXAM_PART, LEGACY_MOJIBAKE_SUBJECT_A_EXAM_PART}
CANONICAL_TOPIC_TAG_ALIASES = (
    (("transaction",), ("transaction",)),
    (("lock", "recovery", "rollback", "commit"), ("transaction",)),
    (("sql", "db", "database"), ("sql",)),
    (("security",), ("security",)),
    (("waf", "ids", "dmz"), ("security",)),
    (("backup", "availability"), ("availability",)),
    (("mtbf", "mttr", "mips", "performance"), ("availability",)),
    (("network",), ("network",)),
    (("sort", "search", "tree", "list", "stack", "algorithm", "pseudo-language", "data structure"), ("algorithm",)),
    (("pert", "man-month", "sla", "cost"), ("project_management", "service_management")),
    (("break-even", "roi", "sales", "profit"), ("topic_0ca193e39c",)),
    (("law", "public question", "weak categories", "monthly review", "july planning"), ("topic_51357175b8",)),
)
SEARCH_KEYWORD_ALIASES = (
    (("project",), "プロジェクトマネジメント"),
    (("service management",), "サービスマネジメント"),
    (("pert", "man-month", "cost"), "プロジェクトマネジメント"),
    (("sla",), "サービスマネジメント"),
    (("waf", "ids", "dmz", "security"), "security"),
    (("backup", "availability"), "availability"),
    (("mtbf", "mttr", "mips", "performance"), "availability"),
    (("network",), "network"),
    (("db", "database"), "SQL"),
    (("sort", "search", "tree", "list", "stack", "algorithm", "pseudo-language", "data structure"), "アルゴリズム"),
    (("audit",), "システム監査"),
    (("break-even",), "損益分岐点"),
    (("roi", "sales", "profit"), "会計・財務"),
    (("law",), "セキュリティ関連法規"),
    (("public question", "weak categories", "monthly review", "july planning"), "security"),
)
FALLBACK_CANDIDATE_SEARCH_PAYLOADS: tuple[dict[str, Any], ...] = (
    {"keywords": ["security"], "topicTags": ["security"], "examPart": SUBJECT_A_EXAM_PART, "limit": 20},
    {"keywords": ["availability"], "topicTags": ["availability"], "examPart": SUBJECT_A_EXAM_PART, "limit": 20},
    {"keywords": ["SQL"], "topicTags": ["sql"], "examPart": SUBJECT_A_EXAM_PART, "limit": 20},
    {"keywords": ["network"], "topicTags": ["network"], "examPart": SUBJECT_A_EXAM_PART, "limit": 20},
    {"keywords": ["会計・財務"], "topicTags": ["topic_0ca193e39c"], "examPart": SUBJECT_A_EXAM_PART, "limit": 20},
    {"keywords": ["セキュリティ関連法規"], "topicTags": ["topic_51357175b8"], "examPart": SUBJECT_A_EXAM_PART, "limit": 20},
)


def parse_practice_focus(practice_focus: str) -> list[FocusTarget]:
    text = practice_focus.strip()
    if not text:
        raise ValueError("practice focus must not be blank")

    parts = [part.strip() for part in text.split(",") if part.strip()]
    matches = [FOCUS_PART_PATTERN.match(part) for part in parts]
    if all(match is None for match in matches):
        return [FocusTarget(label=text, count=10)]

    targets: list[FocusTarget] = []

    for part, match in zip(parts, matches, strict=True):
        if match is None:
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
        keywords = _keywords_for_label(target.label)
        payload = {
            "keywords": keywords,
            "examPart": SUBJECT_A_EXAM_PART,
            "limit": max(target.count * 5, 10),
        }
        topic_tags = _topic_tags_for_label(target.label)
        if topic_tags:
            payload["topicTags"] = topic_tags
        payloads.append(payload)
    return payloads


def build_fallback_candidate_search_payloads() -> list[dict[str, Any]]:
    return [dict(payload) for payload in FALLBACK_CANDIDATE_SEARCH_PAYLOADS]


def _keywords_for_label(label: str) -> list[str]:
    normalized = label.casefold()
    for needles, keyword in SEARCH_KEYWORD_ALIASES:
        if any(needle in normalized for needle in needles):
            return [keyword]
    return [label]


def _topic_tags_for_label(label: str) -> list[str]:
    normalized = label.casefold()
    tags: list[str] = []
    for needles, topic_tags in CANONICAL_TOPIC_TAG_ALIASES:
        if not any(needle in normalized for needle in needles):
            continue
        for topic_tag in topic_tags:
            if topic_tag not in tags:
                tags.append(topic_tag)
    return tags


def select_subject_a_questions(
    candidate_groups: list[list[dict[str, Any]]],
    *,
    required_count: int | None = None,
    focus_targets: list[FocusTarget] | None = None,
) -> list[dict[str, Any]]:
    if required_count is None:
        required_count = sum(target.count for target in focus_targets) if focus_targets is not None else 10

    selected: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    if focus_targets is not None:
        for group, target in zip(candidate_groups, focus_targets, strict=False):
            _append_unique_subject_a_questions(
                selected,
                seen_urls,
                group,
                remaining_count=target.count,
            )
        if len(selected) == required_count:
            return selected

    for group in candidate_groups:
        _append_unique_subject_a_questions(
            selected,
            seen_urls,
            group,
            remaining_count=required_count - len(selected),
        )
        if len(selected) == required_count:
            return selected

    raise InsufficientQuestionsError(
        f"needed {required_count} {SUBJECT_A_EXAM_PART} questions, found {len(selected)}"
    )


def _append_unique_subject_a_questions(
    selected: list[dict[str, Any]],
    seen_urls: set[str],
    candidates: list[dict[str, Any]],
    *,
    remaining_count: int,
) -> None:
    if remaining_count <= 0:
        return

    added = 0
    for question in candidates:
        if question.get("examPart") not in SUBJECT_A_EXAM_PARTS:
            continue
        url = question.get("url")
        if not isinstance(url, str) or not url:
            continue
        if url in seen_urls:
            continue
        selected.append(question)
        seen_urls.add(url)
        added += 1
        if added == remaining_count:
            return
