import pytest

from fe_daily.locks import DailyRunLock, DailyRunLockError


def test_daily_run_lock_blocks_second_concurrent_acquire(tmp_path):
    lock_path = tmp_path / "locks" / "daily_publish.lock"

    with DailyRunLock(lock_path):
        with pytest.raises(DailyRunLockError):
            with DailyRunLock(lock_path):
                pass


def test_daily_run_lock_releases_after_context(tmp_path):
    lock_path = tmp_path / "locks" / "daily_publish.lock"

    with DailyRunLock(lock_path):
        pass

    with DailyRunLock(lock_path):
        assert lock_path.exists()
