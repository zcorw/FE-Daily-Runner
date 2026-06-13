from pathlib import Path

import pytest

from fe_daily.page_renderer import TemplateLoadError, load_template_environment


ROOT = Path(__file__).resolve().parents[1]


def test_required_templates_exist():
    for template_name in [
        "base.html.j2",
        "daily_page.html.j2",
        "index_page.html.j2",
        "progress_entry.md.j2",
        "telegram_message.html.j2",
    ]:
        assert (ROOT / "templates" / template_name).is_file()


def test_load_template_environment_loads_required_template():
    environment = load_template_environment(ROOT / "templates")

    assert environment.get_template("daily_page.html.j2").name == "daily_page.html.j2"


def test_load_template_environment_reports_missing_template_directory(tmp_path):
    with pytest.raises(TemplateLoadError):
        load_template_environment(tmp_path / "missing")
