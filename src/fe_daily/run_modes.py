from dataclasses import dataclass
from enum import Enum

from fe_daily.config import RunMode


class OutputKind(str, Enum):
    TEMP_JSON = "temp_json"
    TEMP_PAGE_PREVIEW = "temp_page_preview"
    DAILY_PAGE = "daily_page"
    INDEX_PAGE = "index_page"
    PROGRESS = "progress"
    STATE = "state"
    RUN_LOG = "run_log"
    TELEGRAM_MESSAGE = "telegram_message"


@dataclass(frozen=True)
class RunModePlan:
    mode: RunMode
    allowed_outputs: frozenset[OutputKind]
    writes_formal_outputs: bool
    sends_telegram: bool
    requires_successful_write_before_notify: bool


def plan_for_run_mode(mode: RunMode) -> RunModePlan:
    if mode is RunMode.DRY_RUN:
        return RunModePlan(
            mode=mode,
            allowed_outputs=frozenset(
                {
                    OutputKind.TEMP_JSON,
                    OutputKind.TEMP_PAGE_PREVIEW,
                    OutputKind.RUN_LOG,
                }
            ),
            writes_formal_outputs=False,
            sends_telegram=False,
            requires_successful_write_before_notify=False,
        )

    formal_outputs = frozenset(
        {
            OutputKind.DAILY_PAGE,
            OutputKind.INDEX_PAGE,
            OutputKind.PROGRESS,
            OutputKind.STATE,
            OutputKind.RUN_LOG,
        }
    )

    if mode is RunMode.WRITE:
        return RunModePlan(
            mode=mode,
            allowed_outputs=formal_outputs,
            writes_formal_outputs=True,
            sends_telegram=False,
            requires_successful_write_before_notify=False,
        )

    if mode is RunMode.NOTIFY:
        return RunModePlan(
            mode=mode,
            allowed_outputs=formal_outputs | frozenset({OutputKind.TELEGRAM_MESSAGE}),
            writes_formal_outputs=True,
            sends_telegram=True,
            requires_successful_write_before_notify=True,
        )

    raise ValueError(f"Unsupported run mode: {mode}")
