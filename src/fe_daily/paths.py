from datetime import date
from enum import Enum
from pathlib import Path

from fe_daily.config import ExistingPagePolicy


class OutputPathError(ValueError):
    pass


class ExistingOutputDecision(str, Enum):
    WRITE = "write"
    SKIP = "skip"


def ensure_within_base(base: Path | str, target: Path | str) -> Path:
    resolved_base = Path(base).resolve()
    resolved_target = Path(target).resolve()

    if resolved_target == resolved_base or resolved_base in resolved_target.parents:
        return resolved_target

    raise OutputPathError(f"Output path escapes configured base: {resolved_target}")


def daily_page_path(output_dir: Path | str, target_date: date) -> Path:
    base = Path(output_dir)
    target = (
        base
        / "daily"
        / f"{target_date:%Y}"
        / f"{target_date:%m}"
        / f"{target_date:%Y-%m-%d}"
        / "index.html"
    )
    return ensure_within_base(base, target)


def index_page_path(output_dir: Path | str) -> Path:
    base = Path(output_dir)
    return ensure_within_base(base, base / "index.html")


def resolve_existing_output(
    target: Path | str,
    policy: ExistingPagePolicy,
) -> ExistingOutputDecision:
    path = Path(target)
    if not path.exists():
        return ExistingOutputDecision.WRITE

    if policy is ExistingPagePolicy.FAIL:
        raise FileExistsError(f"Output already exists: {path}")

    if policy is ExistingPagePolicy.SKIP:
        return ExistingOutputDecision.SKIP

    if policy is ExistingPagePolicy.OVERWRITE:
        return ExistingOutputDecision.WRITE

    raise ValueError(f"Unsupported existing page policy: {policy}")
