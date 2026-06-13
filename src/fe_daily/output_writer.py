import os
import tempfile
from pathlib import Path
from typing import Callable, Protocol


class AtomicWriteError(OSError):
    pass


class ErrorLogger(Protocol):
    def error(self, message: str, *args: object, **kwargs: object) -> None:
        pass


ReplaceCallable = Callable[[str, str], None]


def atomic_write_text(
    target: str | Path,
    content: str,
    *,
    logger: ErrorLogger | None = None,
    replace: ReplaceCallable = os.replace,
) -> None:
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target_path.parent,
            prefix=f".{target_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        replace(str(temp_path), str(target_path))
    except OSError as exc:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        if logger is not None:
            logger.error("atomic write failed for %s", target_path)
        raise AtomicWriteError(f"Failed to atomically write {target_path}") from exc
