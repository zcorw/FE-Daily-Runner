from collections.abc import Iterable


SENSITIVE_KEY_MARKERS = (
    "OPENAI_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "ADMIN_API_TOKEN",
)


class SecretLeakError(ValueError):
    pass


def assert_no_secret_leakage(
    text: str,
    *,
    known_secret_values: Iterable[str] = (),
) -> None:
    for marker in SENSITIVE_KEY_MARKERS:
        if marker in text:
            raise SecretLeakError(f"output contains sensitive key marker: {marker}")

    for secret_value in known_secret_values:
        if secret_value and secret_value in text:
            raise SecretLeakError("output contains a known secret value")
