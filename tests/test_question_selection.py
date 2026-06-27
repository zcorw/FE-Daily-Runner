import pytest

from fe_daily.question_selection import (
    FocusTarget,
    InsufficientQuestionsError,
    build_candidate_search_payloads,
    build_fallback_candidate_search_payloads,
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
        {"keywords": ["SQL join/group"], "topicTags": ["sql"], "examPart": "科目A", "limit": 20},
        {"keywords": ["SQL"], "topicTags": ["sql"], "examPart": "科目A", "limit": 10},
    ]


def test_build_candidate_search_payloads_adds_canonical_topic_tags():
    targets = parse_practice_focus("Transaction 4, lock/recovery 3, SQL 2, security 1")

    payloads = build_candidate_search_payloads(targets)

    assert payloads == [
        {"keywords": ["Transaction"], "topicTags": ["transaction"], "examPart": "科目A", "limit": 20},
        {"keywords": ["lock/recovery"], "topicTags": ["transaction"], "examPart": "科目A", "limit": 15},
        {"keywords": ["SQL"], "topicTags": ["sql"], "examPart": "科目A", "limit": 10},
        {"keywords": ["security"], "topicTags": ["security"], "examPart": "科目A", "limit": 10},
    ]


def test_build_candidate_search_payloads_normalizes_compound_security_and_backup_labels():
    targets = parse_practice_focus("WAF/IDS/DMZ 3, security management 3, audit/backup 2")

    payloads = build_candidate_search_payloads(targets)

    assert payloads == [
        {"keywords": ["security"], "topicTags": ["security"], "examPart": "科目A", "limit": 15},
        {"keywords": ["security"], "topicTags": ["security"], "examPart": "科目A", "limit": 15},
        {"keywords": ["availability"], "topicTags": ["availability"], "examPart": "科目A", "limit": 10},
    ]


def test_build_candidate_search_payloads_maps_management_plan_labels_to_runtime_keywords():
    targets = parse_practice_focus("Project 3, service management 3, audit 2, security 2")

    payloads = build_candidate_search_payloads(targets)

    assert payloads == [
        {"keywords": ["プロジェクトマネジメント"], "examPart": "科目A", "limit": 15},
        {"keywords": ["サービスマネジメント"], "examPart": "科目A", "limit": 15},
        {"keywords": ["システム監査"], "examPart": "科目A", "limit": 10},
        {"keywords": ["security"], "topicTags": ["security"], "examPart": "科目A", "limit": 10},
    ]


def test_build_candidate_search_payloads_maps_strategy_calculation_plan_labels_to_runtime_keywords():
    targets = parse_practice_focus("Break-even 3, ROI 3, sales/profit 2, law 2")

    payloads = build_candidate_search_payloads(targets)

    assert payloads == [
        {"keywords": ["損益分岐点"], "topicTags": ["topic_0ca193e39c"], "examPart": "科目A", "limit": 15},
        {"keywords": ["会計・財務"], "topicTags": ["topic_0ca193e39c"], "examPart": "科目A", "limit": 15},
        {"keywords": ["会計・財務"], "topicTags": ["topic_0ca193e39c"], "examPart": "科目A", "limit": 10},
        {"keywords": ["セキュリティ関連法規"], "topicTags": ["topic_51357175b8"], "examPart": "科目A", "limit": 10},
    ]


def test_build_candidate_search_payloads_maps_management_calculation_plan_labels_to_runtime_keywords():
    targets = parse_practice_focus("PERT 3, man-month/cost 3, SLA 2, DB 2")

    payloads = build_candidate_search_payloads(targets)

    assert payloads == [
        {
            "keywords": ["プロジェクトマネジメント"],
            "topicTags": ["project_management", "service_management"],
            "examPart": "科目A",
            "limit": 15,
        },
        {
            "keywords": ["プロジェクトマネジメント"],
            "topicTags": ["project_management", "service_management"],
            "examPart": "科目A",
            "limit": 15,
        },
        {"keywords": ["サービスマネジメント"], "topicTags": ["project_management", "service_management"], "examPart": "科目A", "limit": 10},
        {"keywords": ["SQL"], "topicTags": ["sql"], "examPart": "科目A", "limit": 10},
    ]


def test_build_fallback_candidate_search_payloads_returns_independent_payloads():
    first = build_fallback_candidate_search_payloads()
    second = build_fallback_candidate_search_payloads()
    first[0]["limit"] = 1

    assert second[0]["limit"] == 20
    assert all(payload["examPart"] == "科目A" for payload in second)


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


def test_select_subject_a_questions_honors_focus_target_counts():
    group_one = [
        {"url": f"https://example.test/sql{i}", "examPart": "科目A"}
        for i in range(1, 8)
    ]
    group_two = [
        {"url": f"https://example.test/law{i}", "examPart": "科目A"}
        for i in range(1, 8)
    ]

    selected = select_subject_a_questions(
        [group_one, group_two],
        focus_targets=[
            FocusTarget(label="SQL", count=4),
            FocusTarget(label="law", count=2),
        ],
    )

    assert [question["url"] for question in selected] == [
        "https://example.test/sql1",
        "https://example.test/sql2",
        "https://example.test/sql3",
        "https://example.test/sql4",
        "https://example.test/law1",
        "https://example.test/law2",
    ]


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
