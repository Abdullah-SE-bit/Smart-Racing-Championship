"""Exercise the CI test runner in isolated repositories, not game behavior."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


RUNNER = Path(__file__).resolve().parents[2] / "scripts/run_tests.py"


def run_isolated(tmp_path: Path, status: str, test_source: str | None) -> subprocess.CompletedProcess:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copyfile(RUNNER, scripts / "run_tests.py")
    docs = tmp_path / "docs/development"
    docs.mkdir(parents=True)
    manifest = {
        "schema_version": 1,
        "features": {"runner_fixture": {"status": status, "test_paths": ["tests/test_gate.py"]}},
    }
    (docs / "validation.json").write_text(json.dumps(manifest), encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    if test_source is not None:
        (tests / "test_gate.py").write_text(test_source, encoding="utf-8")
    environment = os.environ.copy()
    environment.pop("GITHUB_STEP_SUMMARY", None)
    environment.pop("PYTEST_ADDOPTS", None)
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return subprocess.run(
        [sys.executable, str(scripts / "run_tests.py")],
        cwd=tmp_path, capture_output=True, text=True, timeout=30, env=environment,
    )


def test_empty_pending_suite_is_reported_without_claiming_pass(tmp_path: Path) -> None:
    result = run_isolated(tmp_path, "pending", None)
    assert result.returncode == 0
    assert "no tests collected (pytest exit 5)" in result.stdout
    assert "no feature tests passed" in result.stdout
    assert "Discovered pytest suite passed" not in result.stdout


def test_activated_missing_suite_fails(tmp_path: Path) -> None:
    result = run_isolated(tmp_path, "implemented", None)
    assert result.returncode == 1
    assert "FAILED: activated gate" in result.stdout


def test_activated_passing_suite_succeeds(tmp_path: Path) -> None:
    result = run_isolated(
        tmp_path, "implemented",
        "def test_roundtrip(tmp_path):\n"
        "    path = tmp_path / 'fixture.txt'\n"
        "    path.write_text('runner fixture', encoding='utf-8')\n"
        "    assert path.read_text(encoding='utf-8') == 'runner fixture'\n",
    )
    assert result.returncode == 0
    assert "Discovered pytest suite passed" in result.stdout
    assert "FAILED: activated gate" not in result.stdout


@pytest.mark.parametrize("status", ["pending", "implemented"])
def test_test_failures_are_never_suppressed(tmp_path: Path, status: str) -> None:
    result = run_isolated(tmp_path, status, "def test_failure():\n    raise AssertionError('regression sentinel')\n")
    assert result.returncode == 1
    assert "regression sentinel" in result.stdout


def test_activated_wholly_skipped_file_fails(tmp_path: Path) -> None:
    result = run_isolated(
        tmp_path, "implemented",
        "import pytest\n@pytest.mark.skip(reason='runner regression fixture')\ndef test_skipped():\n    return\n",
    )
    assert result.returncode == 1
    assert "FAILED: activated gate" in result.stdout


def test_collection_errors_fail_even_with_pending_features(tmp_path: Path) -> None:
    result = run_isolated(tmp_path, "pending", "raise RuntimeError('collection sentinel')\n")
    assert result.returncode != 0
    assert "collection sentinel" in result.stdout
