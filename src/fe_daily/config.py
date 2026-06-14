from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunMode(str, Enum):
    DRY_RUN = "dry-run"
    WRITE = "write"
    NOTIFY = "notify"


class ExistingPagePolicy(str, Enum):
    FAIL = "fail"
    SKIP = "skip"
    OVERWRITE = "overwrite"


class DailyRunnerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tz: str = "Asia/Tokyo"

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.5"
    openai_reasoning_effort: str = "low"
    openai_text_verbosity: str = "medium"

    question_bank_service_url: str = "http://question-bank-runtime:8000"
    question_bank_timeout_seconds: int = Field(default=20, gt=0)
    question_bank_retry_count: int = Field(default=2, ge=0)

    page_base_url: str | None = None
    telegram_bot_token: SecretStr | None = None
    telegram_chat_id: SecretStr | None = None

    output_dir: Path = Path("site")
    template_dir: Path = Path("templates")
    markdown_compat_enabled: bool = False
    markdown_output_dir: Path = Path("docs")
    study_plan_path: Path = Path("references/legacy-project/june-study-plan.md")
    weak_points_path: Path = Path("references/personal-context/weak_points.md")
    mistake_log_path: Path = Path("references/personal-context/mistake_log.md")
    progress_context_path: Path = Path("references/personal-context/progress.md")
    asset_proxy_base_path: str = "/assets/fe-siken"
    run_mode: RunMode = RunMode.DRY_RUN
    existing_page_policy: ExistingPagePolicy = ExistingPagePolicy.FAIL

    @field_validator(
        "tz",
        "openai_model",
        "openai_reasoning_effort",
        "openai_text_verbosity",
        "question_bank_service_url",
        "asset_proxy_base_path",
        mode="before",
    )
    @classmethod
    def reject_blank_strings(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            raise ValueError("value must not be blank")
        return value

    @field_validator(
        "output_dir",
        "template_dir",
        "markdown_output_dir",
        "study_plan_path",
        "weak_points_path",
        "mistake_log_path",
        "progress_context_path",
        mode="before",
    )
    @classmethod
    def reject_blank_paths(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            raise ValueError("path must not be blank")
        return value


def load_settings(**overrides: Any) -> DailyRunnerSettings:
    return DailyRunnerSettings(**overrides)
