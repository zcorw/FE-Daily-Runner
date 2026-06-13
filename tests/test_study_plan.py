from datetime import date

from fe_daily.study_plan import load_study_plan_entry


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
