from datetime import date

import pytest

from fe_daily.cli import build_parser, main, parse_args
from fe_daily.config import RunMode


def test_parse_date_and_dry_run_mode():
    args = parse_args(["--date", "2026-06-13", "--dry-run"])

    assert args.target_date == date(2026, 6, 13)
    assert args.today is False
    assert args.run_mode is RunMode.DRY_RUN


def test_parse_today_and_write_mode():
    args = parse_args(["--today", "--write"])

    assert args.target_date is None
    assert args.today is True
    assert args.run_mode is RunMode.WRITE


def test_date_and_today_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        parse_args(["--date", "2026-06-13", "--today", "--dry-run"])


def test_run_modes_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        parse_args(["--date", "2026-06-13", "--dry-run", "--write"])


def test_render_only_requires_input():
    with pytest.raises(SystemExit):
        parse_args(["--render-only"])


def test_input_requires_render_only():
    with pytest.raises(SystemExit):
        parse_args(["--input", "tmp/daily.json"])


def test_maintenance_operations_conflict_with_run_modes():
    with pytest.raises(SystemExit):
        parse_args(["--health-check", "--dry-run"])

    with pytest.raises(SystemExit):
        parse_args(["--validate-config", "--notify"])


def test_validate_config_reports_openai_dry_run_limitation(capsys):
    exit_code = main(["--validate-config"], settings_overrides={"_env_file": None})

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000" in captured.out
    assert "OPENAI_API_KEY missing" in captured.out


def test_parser_exposes_expected_options():
    help_text = build_parser().format_help()

    for option in [
        "--date",
        "--today",
        "--dry-run",
        "--write",
        "--notify",
        "--health-check",
        "--validate-config",
        "--render-only",
        "--input",
    ]:
        assert option in help_text
