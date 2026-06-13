import tomllib
from pathlib import Path


def load_pyproject():
    root = Path(__file__).resolve().parents[1]
    return tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))


def test_pyproject_declares_python_package_metadata():
    pyproject = load_pyproject()

    assert pyproject["project"]["name"] == "fe-daily-runner"
    assert pyproject["project"]["requires-python"] == ">=3.11"
    assert pyproject["tool"]["setuptools"]["package-dir"] == {"": "src"}
    assert pyproject["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]


def test_pyproject_configures_pytest():
    pyproject = load_pyproject()

    pytest_options = pyproject["tool"]["pytest"]["ini_options"]

    assert pytest_options["testpaths"] == ["tests"]
    assert "src" in pytest_options["pythonpath"]
