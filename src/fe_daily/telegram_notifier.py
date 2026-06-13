from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import httpx

from fe_daily.page_renderer import load_template_environment


class ErrorLogger(Protocol):
    def error(self, message: str, *args: object, **kwargs: object) -> None:
        pass


@dataclass(frozen=True)
class TelegramSendResult:
    status: str
    message: str


def render_telegram_message(
    *,
    date: str,
    main_theme: str,
    page_url: str,
    template_dir: str | Path,
) -> str:
    environment = load_template_environment(template_dir)
    template = environment.get_template("telegram_message.html.j2")
    return template.render(date=date, main_theme=main_theme, page_url=page_url)


class TelegramNotifier:
    def __init__(
        self,
        *,
        bot_token: str,
        chat_id: str,
        client: httpx.Client | None = None,
        logger: ErrorLogger | None = None,
    ) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.client = client or httpx.Client(base_url="https://api.telegram.org", timeout=20)
        self.logger = logger

    def send_html_message(self, html: str) -> TelegramSendResult:
        response = self.client.post(
            f"/bot{self.bot_token}/sendMessage",
            json={
                "chat_id": self.chat_id,
                "text": html,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
        )
        if response.status_code >= 400:
            if self.logger is not None:
                self.logger.error("Telegram sendMessage failed with status %s", response.status_code)
            return TelegramSendResult(status="failed", message=f"telegram failed: {response.status_code}")

        payload = response.json()
        if payload.get("ok") is not True:
            if self.logger is not None:
                self.logger.error("Telegram sendMessage returned ok=false")
            return TelegramSendResult(status="failed", message="telegram failed: ok=false")

        return TelegramSendResult(status="sent", message="telegram sent")
