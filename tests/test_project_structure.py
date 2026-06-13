from pathlib import Path


def test_project_scaffold_exists():
    root = Path(__file__).resolve().parents[1]

    expected_directories = [
        root / "src" / "fe_daily",
        root / "scripts",
        root / "tests",
        root / "templates",
        root / "config",
        root / "site",
        root / "state",
        root / "logs" / "daily_publish",
    ]

    missing = [path for path in expected_directories if not path.is_dir()]

    assert missing == []


def test_fe_daily_package_has_init_file():
    root = Path(__file__).resolve().parents[1]

    assert (root / "src" / "fe_daily" / "__init__.py").is_file()
