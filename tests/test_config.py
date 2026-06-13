from pathlib import Path

import pytest
from pydantic import ValidationError

from fe_daily.config import ExistingPagePolicy, RunMode, load_settings


def test_load_settings_uses_safe_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    settings = load_settings(
        _env_file=None,
        output_dir=tmp_path / "site",
        template_dir=tmp_path / "templates",
    )

    assert settings.question_bank_service_url == "http://question-bank-runtime:8000"
    assert settings.question_bank_timeout_seconds == 20
    assert settings.question_bank_retry_count == 2
    assert settings.openai_model == "gpt-5.5"
    assert settings.openai_reasoning_effort == "low"
    assert settings.openai_text_verbosity == "medium"
    assert settings.run_mode is RunMode.DRY_RUN
    assert settings.existing_page_policy is ExistingPagePolicy.FAIL
    assert settings.asset_proxy_base_path == "/assets/fe-siken"
    assert settings.output_dir == tmp_path / "site"
    assert settings.template_dir == tmp_path / "templates"
    assert settings.markdown_compat_enabled is False
    assert settings.markdown_output_dir == Path("docs")


def test_load_settings_reads_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "QUESTION_BANK_SERVICE_URL=http://runtime.example:8000",
                "RUN_MODE=write",
                "EXISTING_PAGE_POLICY=overwrite",
                "OPENAI_API_KEY=sk-test-secret",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_settings(_env_file=env_file)

    assert settings.question_bank_service_url == "http://runtime.example:8000"
    assert settings.run_mode is RunMode.WRITE
    assert settings.existing_page_policy is ExistingPagePolicy.OVERWRITE
    assert settings.openai_api_key is not None
    assert settings.openai_api_key.get_secret_value() == "sk-test-secret"


def test_load_settings_rejects_invalid_enums():
    with pytest.raises(ValidationError):
        load_settings(_env_file=None, run_mode="publish")

    with pytest.raises(ValidationError):
        load_settings(_env_file=None, existing_page_policy="replace")


def test_load_settings_rejects_blank_required_values():
    with pytest.raises(ValidationError):
        load_settings(_env_file=None, question_bank_service_url="")

    with pytest.raises(ValidationError):
        load_settings(_env_file=None, output_dir="")


def test_settings_repr_redacts_secrets():
    settings = load_settings(
        _env_file=None,
        openai_api_key="sk-test-secret",
        telegram_bot_token="telegram-secret",
        telegram_chat_id="123456",
    )

    rendered = repr(settings)

    assert "sk-test-secret" not in rendered
    assert "telegram-secret" not in rendered
    assert "123456" not in rendered
    assert "SecretStr" in rendered


def test_settings_paths_are_path_objects():
    settings = load_settings(_env_file=None, output_dir="site", template_dir="templates")

    assert isinstance(settings.output_dir, Path)
    assert isinstance(settings.template_dir, Path)
