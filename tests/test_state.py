import json
from datetime import date

from fe_daily.state import update_daily_state


def test_update_daily_state_writes_current_and_legacy_files(tmp_path):
    state_path = tmp_path / "state" / "daily_state.json"
    legacy_state_path = tmp_path / ".codex" / "daily_state.json"

    update_daily_state(
        state_path=state_path,
        legacy_state_path=legacy_state_path,
        target_date=date(2026, 6, 13),
        daily_page="/daily/2026-06-13/",
        topics=["SQL", "GROUP BY"],
        question_count=10,
        status="success",
    )

    state = json.loads(state_path.read_text(encoding="utf-8"))
    legacy_state = json.loads(legacy_state_path.read_text(encoding="utf-8"))

    assert state == legacy_state
    assert state["last_run_date"] == "2026-06-13"
    assert state["last_daily_page"] == "/daily/2026-06-13/"
    assert state["last_topics"] == ["SQL", "GROUP BY"]
    assert state["last_question_count"] == 10
    assert state["status"] == "success"


def test_update_daily_state_preserves_existing_unrelated_fields(tmp_path):
    state_path = tmp_path / "state" / "daily_state.json"
    state_path.parent.mkdir()
    state_path.write_text('{"custom": "keep"}', encoding="utf-8")

    update_daily_state(
        state_path=state_path,
        legacy_state_path=None,
        target_date=date(2026, 6, 13),
        daily_page="/daily/2026-06-13/",
        topics=["SQL"],
        question_count=10,
        status="success",
    )

    state = json.loads(state_path.read_text(encoding="utf-8"))

    assert state["custom"] == "keep"
    assert state["last_run_date"] == "2026-06-13"
