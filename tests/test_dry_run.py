from datetime import date

from fe_daily.dry_run import write_dry_run_artifacts
from fe_daily.paths import daily_page_path


def test_write_dry_run_artifacts_writes_debug_files_under_tmp(tmp_path):
    paths = write_dry_run_artifacts(
        output_dir=tmp_path / "site",
        target_date=date(2026, 6, 13),
        raw_output={"raw": True},
        validated_output={"title": "Daily FE Study"},
        preview_html="<html>preview</html>",
    )

    assert paths.raw_json.read_text(encoding="utf-8") == '{\n  "raw": true\n}'
    assert paths.validated_json.read_text(encoding="utf-8") == '{\n  "title": "Daily FE Study"\n}'
    assert paths.preview_html.read_text(encoding="utf-8") == "<html>preview</html>"
    assert "/tmp/dry-run/2026-06-13/" in paths.preview_html.as_posix()


def test_write_dry_run_artifacts_does_not_write_formal_daily_page(tmp_path):
    output_dir = tmp_path / "site"

    write_dry_run_artifacts(
        output_dir=output_dir,
        target_date=date(2026, 6, 13),
        raw_output={"raw": True},
        validated_output={"title": "Daily FE Study"},
        preview_html="<html>preview</html>",
    )

    assert not daily_page_path(output_dir, date(2026, 6, 13)).exists()
