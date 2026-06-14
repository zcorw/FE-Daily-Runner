from pathlib import Path


ENV_EXAMPLE = Path(__file__).resolve().parents[1] / ".env.example"


def test_env_example_documents_full_real_run_configuration():
    text = ENV_EXAMPLE.read_text(encoding="utf-8")

    for name in [
        "TZ",
        "QUESTION_BANK_SERVICE_URL",
        "QUESTION_BANK_TIMEOUT_SECONDS",
        "QUESTION_BANK_RETRY_COUNT",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_REASONING_EFFORT",
        "OPENAI_TEXT_VERBOSITY",
        "OUTPUT_DIR",
        "TEMPLATE_DIR",
        "STUDY_PLAN_PATH",
        "WEAK_POINTS_PATH",
        "MISTAKE_LOG_PATH",
        "PROGRESS_CONTEXT_PATH",
        "PAGE_BASE_URL",
        "EXISTING_PAGE_POLICY",
        "ASSET_PROXY_BASE_PATH",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]:
        assert f"{name}=" in text


def test_env_example_uses_safe_placeholders_not_real_secrets():
    text = ENV_EXAMPLE.read_text(encoding="utf-8")

    assert "sk-" not in text
    assert "xoxb-" not in text
    assert "123456:" not in text
    assert "change-me" in text
