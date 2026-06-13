from pathlib import Path
from types import TracebackType

from filelock import FileLock, Timeout


class DailyRunLockError(RuntimeError):
    pass


class DailyRunLock:
    def __init__(self, lock_path: str | Path) -> None:
        self.lock_path = Path(lock_path)
        self._lock = FileLock(str(self.lock_path))

    def __enter__(self) -> "DailyRunLock":
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._lock.acquire(timeout=0)
        except Timeout as exc:
            raise DailyRunLockError(f"daily publish lock is already held: {self.lock_path}") from exc
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._lock.release()
