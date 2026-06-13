import pytest

from fe_daily.secrets import SecretLeakError, assert_no_secret_leakage


@pytest.mark.parametrize(
    "text",
    [
        "OPENAI_API_KEY=sk-test",
        "TELEGRAM_BOT_TOKEN=123:abc",
        "ADMIN_API_TOKEN=admin",
    ],
)
def test_assert_no_secret_leakage_rejects_sensitive_key_names(text):
    with pytest.raises(SecretLeakError):
        assert_no_secret_leakage(text)


def test_assert_no_secret_leakage_rejects_known_secret_values():
    with pytest.raises(SecretLeakError):
        assert_no_secret_leakage("message contains real-token", known_secret_values=["real-token"])


def test_assert_no_secret_leakage_accepts_safe_text():
    assert_no_secret_leakage("date=2026-06-13 status=success", known_secret_values=["real-token"])
