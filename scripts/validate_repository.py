"""Validate repository infrastructure; this does not validate game functionality."""

import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_DOCS = (
    "WORKFLOW BRANCHING_STRATEGY CRITICAL_PATH MODULE_OWNERSHIP INTEGRATION_CONTRACTS "
    "TESTING_STRATEGY CI_POLICY DEFINITION_OF_DONE VIVA_PREPARATION DECISIONS GOVERNANCE_STATUS"
).split()


def validate() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = config["project"]
    for key in ("name", "version", "description", "readme", "requires-python", "dependencies"):
        if not project.get(key):
            raise ValueError(f"Missing project metadata: {key}")
    if project["requires-python"] != ">=3.12":
        raise ValueError("Review the Python baseline and CI together before changing it")
    if config["tool"]["setuptools"]["packages"]["find"]["where"] != ["src"]:
        raise ValueError("Expected src package discovery")
    if config["tool"]["pytest"]["ini_options"]["testpaths"] != ["tests"]:
        raise ValueError("Expected automatic test discovery under tests/")
    if (ROOT / ".python-version").read_text().strip() != "3.12":
        raise ValueError("Python version file must match CI baseline")
    requirements = [
        line.strip() for line in (ROOT / "requirements.txt").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if requirements != ["-e .[dev]"]:
        raise ValueError("requirements.txt must delegate constraints to pyproject.toml")

    required = ["README.md", "AGENTS.md", "PROJECT_STRUCTURE.md", project["readme"]]
    required += [f"docs/development/{name}.md" for name in DEVELOPMENT_DOCS]
    required += [f"docs/development/handoffs/HANDOFF_MEMBER_{i}.md" for i in (1, 2, 3)]
    required += [".github/pull_request_template.md", "docs/development/validation.json"]
    required += ["implementation_plan.md", "mandoff.md", "docs/development/issue_registry.json", "docs/development/phase_state.json"]
    required += [f"docs/development/{name}.md" for name in ("ISSUE_REGISTRY", "TASK_DEPENDENCIES", "PHASE_GATE_POLICY", "CONCURRENCY_POLICY", "HANDOFF_POLICY")]
    required += [f"docs/development/handoffs/HANDOFF_{name}.md" for name in ("ABDULLAH", "TAHA", "SHAHEER")]
    for name in required:
        if not (ROOT / name).is_file():
            raise ValueError(f"Missing required file: {name}")
    packages = [ROOT / "src/smart_racing"]
    packages += [p for p in packages[0].rglob("*") if p.is_dir() and "__pycache__" not in p.parts]
    for directory in packages:
        if not (directory / "__init__.py").is_file():
            raise ValueError(f"Missing package initializer: {directory}")

    # Include untracked candidate files locally; on Actions this is the tracked checkout.
    output = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT
    )
    for name in set(output.decode("utf-8").strip("\0").split("\0")):
        path = ROOT / name
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            continue
        if re.search(r"(?m)^(?:<{7}(?:[ \t\r]|$)|={7}\r?$|>{7}(?:[ \t\r]|$)|\|{7}(?:[ \t\r]|$))", text):
            raise ValueError(f"Unresolved merge-conflict marker: {name}")
        if path.suffix == ".md":
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                if "://" in target or target.startswith(("#", "mailto:")):
                    continue
                relative = target.split("#", 1)[0]
                if relative and not (path.parent / relative).exists():
                    raise ValueError(f"Broken documentation link in {name}: {target}")

    # BaseLoader preserves the Actions 'on' key as a string (YAML 1.1 treats it as bool).
    workflow = yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
    if set(workflow["on"]) != {"pull_request", "push", "workflow_dispatch"}:
        raise ValueError("Unexpected CI triggers")
    for event in ("pull_request", "push"):
        if not {"main", "game"} <= set(workflow["on"][event]["branches"]):
            raise ValueError(f"Missing integration branch trigger: {event}")
    if workflow["permissions"] != {"contents": "read"}:
        raise ValueError("CI must use read-only permissions")
    expected = {"Repository Validation", "Python Quality", "Automated Tests", "Integration Validation"}
    if {job["name"] for job in workflow["jobs"].values()} != expected:
        raise ValueError("Stable job names changed: coordinate protection before renaming")
    for job in workflow["jobs"].values():
        for step in job["steps"]:
            if "uses" in step and not re.fullmatch(r"[\w./-]+@[a-f0-9]{40}", step["uses"]):
                raise ValueError("Actions must be pinned to immutable commit SHAs")
            if step.get("uses", "").startswith("actions/setup-python@"):
                if step["with"]["python-version"] != "3.12":
                    raise ValueError("CI Python version must be 3.12")
    for kind in ("feature", "bug", "algorithm"):
        form = yaml.safe_load((ROOT / f".github/ISSUE_TEMPLATE/{kind}.yml").read_text())
        if not all(form.get(key) for key in ("name", "description", "title", "body")):
            raise ValueError(f"Incomplete issue form: {kind}")
        ids = [field["id"] for field in form["body"] if field["type"] != "markdown"]
        if len(set(ids)) != len(ids):
            raise ValueError(f"Duplicate issue form field IDs: {kind}")
    yaml.safe_load((ROOT / ".github/ISSUE_TEMPLATE/config.yml").read_text())
    for filename, expected_name in [("phase-gates.yml", "Phase Gate Validation"), ("issue-gate-audit.yml", "Issue Gate Audit")]:
        policy = yaml.load((ROOT / ".github/workflows" / filename).read_text(), Loader=yaml.BaseLoader)
        if "pull_request_target" in policy["on"] or any(value != "read" for value in policy["permissions"].values()):
            raise ValueError("Phase policy workflows must be read-only and never use privileged PR execution")
        if {job["name"] for job in policy["jobs"].values()} != {expected_name}:
            raise ValueError("Stable phase check name changed")
        for job in policy["jobs"].values():
            for step in job["steps"]:
                if "uses" in step and not re.fullmatch(r"[\w./-]+@[a-f0-9]{40}", step["uses"]):
                    raise ValueError("Phase workflow actions must be SHA-pinned")
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.plan_backlog import parse_plan

    plan = parse_plan(ROOT / "implementation_plan.md")
    registry = json.loads((ROOT / "docs/development/issue_registry.json").read_text())
    if registry["plan_sha256"] != plan["plan_sha256"]:
        raise ValueError("Roadmap changed without a refreshed issue registry")
    if set(registry["issues"]) != set(plan["dependencies"]):
        raise ValueError("Issue registry does not cover every plan task and gate")
    numbers = [entry["number"] for entry in registry["issues"].values()]
    if len(numbers) != len(set(numbers)):
        raise ValueError("Issue numbers must map to unique plan IDs")
    if registry["audit"].get("status") != "VERIFIED":
        raise ValueError("Native dependency audit is incomplete; inspect registry diagnostics")
    manifest = json.loads((ROOT / "docs/development/validation.json").read_text())
    if manifest["schema_version"] != 1 or not manifest["features"]:
        raise ValueError("Invalid validation manifest")
    for name, feature in manifest["features"].items():
        if feature["status"] not in {"pending", "implemented"}:
            raise ValueError(f"Unknown implementation state: {name}")
        if not feature["test_paths"] or any(not p.startswith("tests/") for p in feature["test_paths"]):
            raise ValueError(f"Invalid required test paths: {name}")
    print("Repository infrastructure validated. Feature correctness is not asserted.")


if __name__ == "__main__":
    validate()
