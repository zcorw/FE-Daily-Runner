from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from fe_daily.output_schema import DailyLearningContent


DEFAULT_TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"

REQUIRED_TEMPLATE_NAMES = (
    "base.html.j2",
    "daily_page.html.j2",
    "index_page.html.j2",
    "progress_entry.md.j2",
    "telegram_message.html.j2",
)


class TemplateLoadError(ValueError):
    """Raised when the page template environment cannot be created."""


def load_template_environment(template_dir: str | Path) -> Environment:
    path = Path(template_dir)
    if not path.is_dir():
        raise TemplateLoadError(f"Template directory does not exist: {path}")

    missing_templates = [
        template_name
        for template_name in REQUIRED_TEMPLATE_NAMES
        if not (path / template_name).is_file()
    ]
    if missing_templates:
        missing = ", ".join(missing_templates)
        raise TemplateLoadError(f"Missing required templates: {missing}")

    return Environment(
        loader=FileSystemLoader(path),
        autoescape=select_autoescape(
            enabled_extensions=("html", "xml", "html.j2", "xml.j2"),
            default_for_string=True,
        ),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_daily_page(
    content: DailyLearningContent,
    *,
    template_dir: str | Path = DEFAULT_TEMPLATE_DIR,
) -> str:
    environment = load_template_environment(template_dir)
    template = environment.get_template("daily_page.html.j2")
    return template.render(**_template_context(content))


def _template_context(content: DailyLearningContent) -> dict[str, Any]:
    return content.model_dump(mode="json")
