from fe_daily.cli import main
from fe_daily.health_check import HealthStatus, check_runtime_health
from fe_daily.question_bank_client import QuestionBankHTTPError, QuestionBankTimeoutError


class HealthyClient:
    def health(self):
        return {"ok": True, "database": "ready", "readOnly": True}


class UnhealthyClient:
    def health(self):
        return {"ok": False, "database": "down", "readOnly": True}


class TimeoutClient:
    def health(self):
        raise QuestionBankTimeoutError("GET", "/health", "timed out")


def test_check_runtime_health_reports_ready_service():
    result = check_runtime_health(HealthyClient())

    assert result.status is HealthStatus.OK
    assert result.exit_code == 0
    assert result.message == "question bank runtime is healthy"


def test_check_runtime_health_fails_closed_when_service_reports_not_ok():
    result = check_runtime_health(UnhealthyClient())

    assert result.status is HealthStatus.FAILED
    assert result.exit_code == 1
    assert "not healthy" in result.message


def test_check_runtime_health_fails_closed_on_timeout():
    result = check_runtime_health(TimeoutClient())

    assert result.status is HealthStatus.FAILED
    assert result.exit_code == 1
    assert "timed out" in result.message


def test_cli_health_check_uses_runtime_client_factory(capsys):
    exit_code = main(
        ["--health-check"],
        settings_overrides={"_env_file": None},
        question_bank_client_factory=lambda _settings: HealthyClient(),
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "question bank runtime is healthy" in captured.out


def test_cli_health_check_returns_nonzero_on_runtime_failure(capsys):
    exit_code = main(
        ["--health-check"],
        settings_overrides={"_env_file": None},
        question_bank_client_factory=lambda _settings: TimeoutClient(),
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "timed out" in captured.out


def test_cli_health_check_returns_nonzero_on_http_error(capsys):
    class HTTPErrorClient:
        def health(self):
            raise QuestionBankHTTPError("GET", "/health", 503, "unavailable")

    exit_code = main(
        ["--health-check"],
        settings_overrides={"_env_file": None},
        question_bank_client_factory=lambda _settings: HTTPErrorClient(),
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "HTTP 503" in captured.out
