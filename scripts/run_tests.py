"""Run real pytest discovery and enforce the declared feature test gates."""

import json
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def report(message: str) -> None:
    print(message)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write(message + "\n\n")


class FeatureGates:
    def __init__(self, required_paths: list[str]) -> None:
        self.required_paths = required_paths
        self.collected: set[str] = set()
        self.passed: set[str] = set()

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        self.collected = {item.nodeid.split("::", 1)[0] for item in session.items}

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.when == "call" and report.passed:
            self.passed.add(report.nodeid.split("::", 1)[0])


def main() -> int:
    os.chdir(ROOT)
    features = json.loads((ROOT / "docs/development/validation.json").read_text())["features"]
    required = []
    for name, feature in features.items():
        if feature["status"] == "pending":
            report(f"PENDING: {name} is not implemented or verified.")
        elif feature["status"] == "implemented":
            required.extend(feature["test_paths"])
        else:
            raise ValueError(f"Unknown implementation state: {name}")
    gates = FeatureGates(required)
    result = pytest.main(["tests"], plugins=[gates])
    for pattern in gates.required_paths:
        matching = {p for p in gates.collected if Path(p).match(pattern)}
        if not matching or not matching <= gates.passed:
            report(f"FAILED: activated gate {pattern} needs collected, passing tests in every matching file.")
            return 1
    if result == pytest.ExitCode.NO_TESTS_COLLECTED:
        if required:
            return 1
        report("PENDING: no tests collected (pytest exit 5). Infrastructure may pass; no feature tests passed.")
        return 0
    if result == pytest.ExitCode.OK:
        report("Discovered pytest suite passed. Pending features above remain unverified.")
    return int(result)


if __name__ == "__main__":
    raise SystemExit(main())
