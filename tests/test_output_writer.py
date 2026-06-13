import os

import pytest

from fe_daily.output_writer import AtomicWriteError, atomic_write_text


class CapturingLogger:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, message: str, *args: object, **kwargs: object) -> None:
        self.errors.append(message % args)


def test_atomic_write_text_replaces_target_file(tmp_path):
    target = tmp_path / "daily" / "index.html"
    target.parent.mkdir()
    target.write_text("old", encoding="utf-8")

    atomic_write_text(target, "new")

    assert target.read_text(encoding="utf-8") == "new"


def test_atomic_write_text_keeps_existing_file_and_logs_failure(tmp_path):
    target = tmp_path / "daily" / "index.html"
    target.parent.mkdir()
    target.write_text("old", encoding="utf-8")
    logger = CapturingLogger()

    def failing_replace(source: str, destination: str) -> None:
        raise OSError("replace failed")

    with pytest.raises(AtomicWriteError):
        atomic_write_text(target, "new", logger=logger, replace=failing_replace)

    assert target.read_text(encoding="utf-8") == "old"
    assert logger.errors == [f"atomic write failed for {target}"]
    assert [path for path in target.parent.iterdir()] == [target]


def test_atomic_write_text_creates_parent_directories(tmp_path):
    target = tmp_path / "site" / "daily" / "index.html"

    atomic_write_text(target, "created", replace=os.replace)

    assert target.read_text(encoding="utf-8") == "created"
