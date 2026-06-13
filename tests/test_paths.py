from datetime import date

import pytest

from fe_daily.config import ExistingPagePolicy
from fe_daily.paths import (
    ExistingOutputDecision,
    OutputPathError,
    daily_page_path,
    ensure_within_base,
    index_page_path,
    resolve_existing_output,
)


def test_daily_page_path_is_derived_from_output_root(tmp_path):
    assert daily_page_path(tmp_path, date(2026, 6, 13)) == (
        tmp_path / "daily" / "2026" / "06" / "2026-06-13" / "index.html"
    )


def test_index_page_path_is_derived_from_output_root(tmp_path):
    assert index_page_path(tmp_path) == tmp_path / "index.html"


def test_ensure_within_base_accepts_descendant_paths(tmp_path):
    target = tmp_path / "daily" / "2026" / "page.html"

    assert ensure_within_base(tmp_path, target) == target.resolve()


def test_ensure_within_base_rejects_path_traversal(tmp_path):
    with pytest.raises(OutputPathError):
        ensure_within_base(tmp_path, tmp_path / ".." / "outside.html")


def test_ensure_within_base_rejects_absolute_path_outside_base(tmp_path):
    outside = tmp_path.parent / "outside.html"

    with pytest.raises(OutputPathError):
        ensure_within_base(tmp_path, outside)


def test_existing_output_fail_policy_raises_for_existing_file(tmp_path):
    target = tmp_path / "index.html"
    target.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        resolve_existing_output(target, ExistingPagePolicy.FAIL)


def test_existing_output_skip_policy_skips_existing_file(tmp_path):
    target = tmp_path / "index.html"
    target.write_text("existing", encoding="utf-8")

    assert resolve_existing_output(target, ExistingPagePolicy.SKIP) is ExistingOutputDecision.SKIP


def test_existing_output_overwrite_policy_writes_existing_file(tmp_path):
    target = tmp_path / "index.html"
    target.write_text("existing", encoding="utf-8")

    assert resolve_existing_output(target, ExistingPagePolicy.OVERWRITE) is ExistingOutputDecision.WRITE


def test_existing_output_missing_file_writes_for_any_policy(tmp_path):
    target = tmp_path / "index.html"

    for policy in ExistingPagePolicy:
        assert resolve_existing_output(target, policy) is ExistingOutputDecision.WRITE
