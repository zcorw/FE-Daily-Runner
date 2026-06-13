import pytest

from fe_daily.question_selection import (
    FocusTarget,
    build_candidate_search_payloads,
    parse_practice_focus,
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
