import pytest

from fe_daily.question_selection import (
    FocusTarget,
    InsufficientQuestionsError,
    build_candidate_search_payloads,
    parse_practice_focus,
    select_subject_a_questions,
)


def test_parse_practice_focus_extracts_weighted_targets():
    targets = parse_practice_focus("SQL join/group 4, DB design 2, transaction 2, law 2")

    assert targets == [
        FocusTarget(label="SQL join/group", count=4),
        FocusTarget(label="DB design", count=2),
        FocusTarget(label="transaction", count=2),
        FocusTarget(label="law", count=2),
    ]


def test_parse_practice_focus_handles_public_question_focus_without_count():
    targets = parse_practice_focus("Public questions A first half; classify every missed item")

    assert targets == [FocusTarget(label="Public questions A first half; classify every missed item", count=10)]


def test_parse_practice_focus_handles_comma_separated_review_focus_without_counts():
    focus = "Calculation-only review: base conversion, bit operation, transmission, availability"

    targets = parse_practice_focus(focus)

    assert targets == [FocusTarget(label=focus, count=10)]


def test_parse_practice_focus_rejects_empty_text():
    with pytest.raises(ValueError):
        parse_practice_focus(" ")


def test_build_candidate_search_payloads_use_runtime_api_shape():
    targets = parse_practice_focus("SQL join/group 4, DB design 2")

    payloads = build_candidate_search_payloads(targets)

    assert payloads == [
        {"keywords": ["SQL join/group"], "examPart": "科目A", "limit": 4},
        {"keywords": ["DB design"], "examPart": "科目A", "limit": 2},
    ]


def test_build_candidate_search_payloads_rejects_non_positive_counts():
    with pytest.raises(ValueError):
        build_candidate_search_payloads([FocusTarget(label="SQL", count=0)])


def test_select_subject_a_questions_returns_exactly_required_count():
    candidates = [
        {"url": f"https://example.test/q{i}", "examPart": "科目A"}
        for i in range(12)
    ]

    selected = select_subject_a_questions([candidates], required_count=10)

    assert len(selected) == 10
    assert selected == candidates[:10]


def test_select_subject_a_questions_filters_non_subject_a_and_dedupes_urls():
    group_one = [
        {"url": "https://example.test/q1", "examPart": "科目A"},
        {"url": "https://example.test/q2", "examPart": "科目B"},
        {"url": "https://example.test/q1", "examPart": "科目A"},
    ]
    group_two = [
        {"url": f"https://example.test/q{i}", "examPart": "科目A"}
        for i in range(3, 12)
    ]

    selected = select_subject_a_questions([group_one, group_two], required_count=10)

    assert [question["url"] for question in selected] == [
        "https://example.test/q1",
        "https://example.test/q3",
        "https://example.test/q4",
        "https://example.test/q5",
        "https://example.test/q6",
        "https://example.test/q7",
        "https://example.test/q8",
        "https://example.test/q9",
        "https://example.test/q10",
        "https://example.test/q11",
    ]


def test_select_subject_a_questions_fails_when_fewer_than_required():
    candidates = [
        {"url": "https://example.test/q1", "examPart": "科目A"},
        {"url": "https://example.test/q2", "examPart": "科目B"},
    ]

    with pytest.raises(InsufficientQuestionsError) as exc_info:
        select_subject_a_questions([candidates], required_count=10)

    assert "needed 10 科目A questions, found 1" in str(exc_info.value)
