from datetime import date

from fe_daily.study_plan import (
    build_fallback_plan_entry,
    ensure_monthly_plan,
    load_study_plan_entry,
    select_study_plan_entry,
)


def test_load_study_plan_entry_reads_june_plan_row(tmp_path):
    plan_path = tmp_path / "june-study-plan.md"
    plan_path.write_text(
        "\n".join(
            [
                "| Date | Main Theme | 20-Minute Reading Assignment | Practice Focus |",
                "|---|---|---|---|",
                "| 2026-06-12 | Network | Ch.5 p.1-6 | network 10 |",
                "| 2026-06-13 | データベース: 集計・結合 | Ch.4.3 SQL集計/結合 p.129-133; Ch.4.5 練習 p.141-143 | SQL join/group 4, DB design 2, transaction 2, law 2 |",
            ]
        ),
        encoding="utf-8",
    )

    entry = load_study_plan_entry(plan_path, date(2026, 6, 13))

    assert entry is not None
    assert entry.date == date(2026, 6, 13)
    assert entry.main_theme == "データベース: 集計・結合"
    assert entry.reading_assignment == "Ch.4.3 SQL集計/結合 p.129-133; Ch.4.5 練習 p.141-143"
    assert entry.practice_focus == "SQL join/group 4, DB design 2, transaction 2, law 2"
    assert entry.plan_source == "june-study-plan"


def test_load_study_plan_entry_returns_none_for_missing_date(tmp_path):
    plan_path = tmp_path / "june-study-plan.md"
    plan_path.write_text(
        "\n".join(
            [
                "| Date | Main Theme | 20-Minute Reading Assignment | Practice Focus |",
                "|---|---|---|---|",
                "| 2026-06-12 | Network | Ch.5 p.1-6 | network 10 |",
            ]
        ),
        encoding="utf-8",
    )

    assert load_study_plan_entry(plan_path, date(2026, 6, 13)) is None


def test_select_study_plan_entry_uses_existing_plan_before_fallback(tmp_path):
    plan_path = tmp_path / "june-study-plan.md"
    plan_path.write_text(
        "\n".join(
            [
                "| Date | Main Theme | 20-Minute Reading Assignment | Practice Focus |",
                "|---|---|---|---|",
                "| 2026-06-13 | データベース: 集計・結合 | Ch.4.3 SQL p.129-133 | SQL join/group 10 |",
            ]
        ),
        encoding="utf-8",
    )

    entry = select_study_plan_entry(
        plan_path,
        date(2026, 6, 13),
        weak_points="- Network routing",
        mistake_log="- Transaction isolation",
        recent_progress="- Practiced security",
    )

    assert entry.main_theme == "データベース: 集計・結合"
    assert entry.plan_source == "june-study-plan"


def test_select_study_plan_entry_falls_back_when_date_missing(tmp_path):
    plan_path = tmp_path / "june-study-plan.md"
    plan_path.write_text(
        "\n".join(
            [
                "| Date | Main Theme | 20-Minute Reading Assignment | Practice Focus |",
                "|---|---|---|---|",
                "| 2026-06-12 | Network | Ch.5 p.1-6 | network 10 |",
            ]
        ),
        encoding="utf-8",
    )

    entry = select_study_plan_entry(
        plan_path,
        date(2026, 6, 13),
        weak_points="- SQL aggregation mistakes",
        mistake_log="- GROUP BY vs WHERE",
        recent_progress="- Finished database normalization",
    )

    assert entry.date == date(2026, 6, 13)
    assert entry.plan_source == "fallback"
    assert "SQL aggregation mistakes" in entry.main_theme
    assert "weak points" in entry.reading_assignment
    assert entry.practice_focus == "SQL aggregation mistakes 10"


def test_select_study_plan_entry_generates_monthly_plan_when_target_month_missing(tmp_path):
    plan_path = tmp_path / "study-plan.md"
    plan_path.write_text(
        "\n".join(
            [
                "| Date | Main Theme | 20-Minute Reading Assignment | Practice Focus |",
                "|---|---|---|---|",
                "| 2026-06-30 | Monthly Review | Review June | security 10 |",
            ]
        ),
        encoding="utf-8",
    )

    entry = select_study_plan_entry(
        plan_path,
        date(2026, 7, 1),
        weak_points="- SQL aggregation mistakes",
        mistake_log="- GROUP BY vs WHERE",
        recent_progress="- Finished database normalization",
    )

    text = plan_path.read_text(encoding="utf-8")
    assert "## Auto-generated Study Plan - 2026-07" in text
    assert "| 2026-07-01 | 弱点補強: SQL aggregation mistakes |" in text
    assert entry.date == date(2026, 7, 1)
    assert entry.practice_focus == "security 4, SQL 2, availability 2, network 2"


def test_ensure_monthly_plan_does_not_rewrite_when_month_exists(tmp_path):
    plan_path = tmp_path / "study-plan.md"
    original = "\n".join(
        [
            "| Date | Main Theme | 20-Minute Reading Assignment | Practice Focus |",
            "|---|---|---|---|",
            "| 2026-07-02 | Existing July Plan | Review | security 10 |",
        ]
    )
    plan_path.write_text(original, encoding="utf-8")

    generated = ensure_monthly_plan(
        plan_path,
        date(2026, 7, 1),
        weak_points="",
        mistake_log="",
        recent_progress="",
    )

    assert generated is False
    assert plan_path.read_text(encoding="utf-8") == original


def test_build_fallback_plan_entry_uses_mistake_log_when_weak_points_empty():
    entry = build_fallback_plan_entry(
        date(2026, 6, 13),
        weak_points="",
        mistake_log="- Transaction isolation",
        recent_progress="- Practiced security",
    )

    assert entry.plan_source == "fallback"
    assert entry.main_theme == "Transaction isolation"
