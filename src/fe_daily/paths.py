from datetime import date
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from fe_daily.config import ExistingPagePolicy


class OutputPathError(ValueError):
    pass


class ExistingOutputDecision(str, Enum):
    WRITE = "write"
    SKIP = "skip"


@dataclass(frozen=True)
class OutputTargets:
    daily_page: Path
    index_page: Path
    markdown_daily_page: Path | None = None
    markdown_index_page: Path | None = None


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


def markdown_daily_page_path(markdown_output_dir: Path | str, target_date: date) -> Path:
    base = Path(markdown_output_dir)
    target = base / "daily" / f"{target_date:%Y}" / f"{target_date:%m}" / f"{target_date:%Y-%m-%d}.md"
    return ensure_within_base(base, target)


def markdown_index_page_path(markdown_output_dir: Path | str) -> Path:
    base = Path(markdown_output_dir)
    return ensure_within_base(base, base / "index.md")


def output_targets(
    output_dir: Path | str,
    target_date: date,
    *,
    markdown_compat_enabled: bool = False,
    markdown_output_dir: Path | str = "docs",
) -> OutputTargets:
    markdown_daily = None
    markdown_index = None
    if markdown_compat_enabled:
        markdown_daily = markdown_daily_page_path(markdown_output_dir, target_date)
        markdown_index = markdown_index_page_path(markdown_output_dir)

    return OutputTargets(
        daily_page=daily_page_path(output_dir, target_date),
        index_page=index_page_path(output_dir),
        markdown_daily_page=markdown_daily,
        markdown_index_page=markdown_index,
    )


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
