import json
from pathlib import Path

import httpx

from fe_daily.telegram_notifier import (
    TelegramNotifier,
    render_failure_telegram_message,
    render_telegram_message,
)


ROOT = Path(__file__).resolve().parents[1]


class CapturingLogger:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, message: str, *args: object, **kwargs: object) -> None:
        self.errors.append(message % args)


def test_render_telegram_message_escapes_html_special_characters():
    html = render_telegram_message(
        date="2026-06-13",
        main_theme="<SQL & DB>",
        page_url="https://example.test/daily/2026-06-13/",
        template_dir=ROOT / "templates",
    )

    assert "&lt;SQL &amp; DB&gt;" in html
    assert "<SQL & DB>" not in html


def test_telegram_notifier_sends_html_without_logging_token_on_failure():
    logger = CapturingLogger()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/botsecret-token/sendMessage"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["chat_id"] == "123"
        assert payload["parse_mode"] == "HTML"
        assert payload["text"] == "<b>Hello</b>"
        return httpx.Response(500, json={"ok": False, "description": "failure"})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.telegram.org")
    notifier = TelegramNotifier(bot_token="secret-token", chat_id="123", client=client, logger=logger)

    result = notifier.send_html_message("<b>Hello</b>")

    assert result.status == "failed"
    assert logger.errors
    assert "secret-token" not in logger.errors[0]


def test_render_failure_telegram_message_redacts_secret_markers():
    html = render_failure_telegram_message(
        date="2026-06-13",
        stage="openai_validation",
        error_summary="OPENAI_API_KEY=sk-secret failed",
    )

    assert "2026-06-13" in html
    assert "openai_validation" in html
    assert "OPENAI_API_KEY" not in html
    assert "sk-secret" not in html
