from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from fe_daily.question_bank_client import QuestionBankError


class HealthStatus(str, Enum):
    OK = "ok"
    FAILED = "failed"


@dataclass(frozen=True)
class HealthCheckResult:
    status: HealthStatus
    exit_code: int
    message: str


class HealthClient(Protocol):
    def health(self) -> dict:
        pass


def check_runtime_health(client: HealthClient) -> HealthCheckResult:
    try:
        payload = client.health()
    except QuestionBankError as exc:
        return HealthCheckResult(
            status=HealthStatus.FAILED,
            exit_code=1,
            message=f"question bank runtime health check failed: {exc}",
        )

    if payload.get("ok") is not True:
        return HealthCheckResult(
            status=HealthStatus.FAILED,
            exit_code=1,
            message=f"question bank runtime is not healthy: {payload}",
        )

    return HealthCheckResult(
        status=HealthStatus.OK,
        exit_code=0,
        message="question bank runtime is healthy",
    )
