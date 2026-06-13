import json
from datetime import date
from pathlib import Path
from typing import Any


def update_daily_state(
    *,
    state_path: str | Path,
    legacy_state_path: str | Path | None,
    target_date: date,
    daily_page: str,
    topics: list[str],
    question_count: int,
    status: str,
) -> dict[str, Any]:
    path = Path(state_path)
    state = _read_json_object(path)
    state.update(
        {
            "last_run_date": target_date.isoformat(),
            "last_daily_page": daily_page,
            "last_topics": topics,
            "last_question_count": question_count,
            "status": status,
        }
    )

    _write_json(path, state)
    if legacy_state_path is not None:
        _write_json(Path(legacy_state_path), state)
    return state


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
