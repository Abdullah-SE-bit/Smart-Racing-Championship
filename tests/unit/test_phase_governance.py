"""Regression tests for phase policy; fixture evidence is never project acceptance."""

import json
from pathlib import Path

import pytest

from scripts.plan_backlog import expand_dependencies, parse_plan, validate_dag
from scripts.sync_backlog import identify, merge_body
from scripts.verify_phase_gates import CI_NAMES, Policy, declaration, validate_maintenance


ROOT = Path(__file__).resolve().parents[2]


def block(marker, data):
    return f"<!-- {marker} -->\n```json\n{json.dumps(data)}\n```"


def test_full_roadmap_coverage_and_optional_scope():
    plan = parse_plan(ROOT / "implementation_plan.md")
    assert len(plan["tasks"]) == 171
    assert len(plan["phases"]) == 16
    assert len(plan["dependencies"]) == 188
    assert sum(map(len, plan["dependencies"].values())) == 582
    assert "04-P05" not in plan["dependencies"]["P04-GATE"]
    assert plan["tasks"]["01-I01"]["owners"] == ["Shaheer", "Taha"]
    assert "01-P04" in plan["tasks"]["01-I01"]["dependencies"]
    assert all(f"P{int(t['phase'])-1:02d}-GATE" in t["dependencies"] for t in plan["tasks"].values())


def test_ranges_expand_without_serializing_parallel_peers():
    assert expand_dependencies("03-C02..04, 03-P01..04") == [
        "03-C02", "03-C03", "03-C04", "03-P01", "03-P02", "03-P03", "03-P04",
    ]
    plan = parse_plan(ROOT / "implementation_plan.md")
    assert "01-P02" not in plan["tasks"]["01-P01"]["dependencies"]


def test_roadmap_fingerprint_is_stable_across_windows_and_linux(tmp_path):
    text = (ROOT / "implementation_plan.md").read_text(encoding="utf-8-sig")
    windows, linux = tmp_path / "windows.md", tmp_path / "linux.md"
    windows.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    linux.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))
    assert parse_plan(windows)["plan_sha256"] == parse_plan(linux)["plan_sha256"]


@pytest.mark.parametrize("graph", [{"a": ["b"], "b": ["a"]}, {"a": ["missing"]}])
def test_invalid_dependency_graph_fails(graph):
    with pytest.raises(ValueError):
        validate_dag(graph)


def test_issue_identity_is_stable_across_open_and_closed_titles():
    for state in ("open", "closed"):
        assert identify({"title": "[P01-C01] Existing task", "state": state}) == "01-C01"
    assert identify({"title": "[P00-GATE] Infrastructure", "body": ""}) == "P00-GATE"
    assert identify({"title": "[P01-C01] PR", "pull_request": {}}) is None
    assert identify({"title": "Renamed", "body": "<!-- plan-task:02-C04 -->"}) == "02-C04"


def test_managed_body_updates_preserve_human_notes_and_are_idempotent():
    existing = "Human context\n\n" + merge_body("", "old") + "\nHuman test evidence"
    updated = merge_body(existing, "new")
    assert updated.startswith("Human context")
    assert updated.endswith("Human test evidence")
    assert "old" not in updated
    assert merge_body(updated, "new") == updated


def test_refresh_does_not_erase_checked_progress():
    old = merge_body("", "- [ ] Actual evidence linked")
    checked = old.replace("- [ ]", "- [x]")
    refreshed = merge_body(checked, "- [ ] Actual evidence linked\nNew metadata")
    assert "- [x] Actual evidence linked" in refreshed


def maintenance():
    return {"classification": "maintenance", "phase": None, "task_ids": [],
            "reason": "Repair CI infrastructure", "risks": "Workflow configuration changes",
            "tests": "pytest and YAML validation", "interfaces": "unchanged", "affected_gate": "P00-GATE"}


def test_maintenance_bootstrap_needs_real_scope_and_excludes_app_files():
    validate_maintenance(maintenance(), "maintenance/coordination", ["docs/development/policy.md", "scripts/check.py"], False)
    with pytest.raises(ValueError, match="never application"):
        validate_maintenance(maintenance(), "maintenance/coordination", ["src/smart_racing/game/race.py"], False)
    with pytest.raises(ValueError, match="fake phase"):
        validate_maintenance({**maintenance(), "task_ids": ["01-C01"]}, "maintenance/x", ["README.md"], False)


def test_missing_or_multiple_declarations_fail_closed():
    with pytest.raises(ValueError):
        declaration("ordinary PR without phase data")
    data = block("phase-governance", maintenance())
    with pytest.raises(ValueError):
        declaration(data + data)
    assert declaration(data)["classification"] == "maintenance"


class EvidenceAPI:
    """A deterministic network fixture for evidence validation, not actual GitHub."""

    def __init__(self):
        self.data = {}

    def request(self, method, path):
        assert method == "GET", "Gate policy must never mutate remote state"
        if path.startswith("compare/"):
            return {"behind_by": 0}
        if path not in self.data:
            raise AssertionError(f"Unexpected API request: {path}")
        return self.data[path]

    def pages(self, path):
        return self.request("GET", path)

    def file(self, path, ref):
        assert path and ref
        return "Fixture documentation; not real acceptance evidence"


def policy_fixture():
    api = EvidenceAPI()
    members = {"Abdullah": {"login": "owner", "handoff": "docs/development/handoffs/HANDOFF_ABDULLAH.md"}}
    state = {"members": members, "authorized_phase": None}
    plan = {
        "phases": {"01": {"tasks": ["01-C01", "01-I02"]}},
        "tasks": {"01-C01": {"phase": "01", "owners": ["Abdullah"], "dependencies": ["P00-GATE"]}},
        "dependencies": {"P00-GATE": [], "P01-GATE": ["01-C01", "01-I02"]},
    }
    registry = {"P00-GATE": {"number": 1}, "P01-GATE": {"number": 2}, "01-C01": {"number": 3}, "01-I02": {"number": 4}}
    for phase, number, commit, promotion in [("00", 1, "main0", 100), ("01", 2, "main1", 101)]:
        evidence = {"status": "accepted", "demo_url": "https://example.test/demo", "test_url": "https://example.test/test",
                    "ci_run_id": 900+number, "handoff_commit": commit, "acceptance_document": "docs/demos/acceptance.md",
                    "approval_comment_id": 800+number, "promotion_pr": promotion, "main_commit": commit,
                    "audit_run_id": 950,
                    "checkpoint_ref": "refs/tags/checkpoint/"+phase}
        api.data[f"issues/{number}"] = {"number": number, "state": "closed", "state_reason": "completed",
            "body": f"<!-- plan-gate:P{phase}-GATE -->\n"+block("gate-evidence", evidence)}
        api.data[f"pulls/{promotion}"] = {"number": promotion, "merged": True, "base": {"ref": "main"},
            "head": {"sha": "head"+phase, "ref": "game"}, "merge_commit_sha": commit, "user": {"login": "author"}}
        api.data[f"pulls/{promotion}/reviews"] = [{"state": "APPROVED", "user": {"login": "teammate", "type": "User"},
            "author_association": "COLLABORATOR", "commit_id": "head"+phase}]
        api.data[f"git/ref/tags/checkpoint/{phase}"] = {"object": {"sha": commit, "type": "commit"}}
        api.data[f"issues/comments/{800+number}"] = {"user": {"type": "User"}, "author_association": "COLLABORATOR",
            "body": f"gate-approved:P{phase}-GATE:{commit}"}
        api.data[f"actions/runs/{900+number}"] = {"head_sha": commit, "status": "completed", "conclusion": "success"}
        api.data[f"commits/{commit}/check-runs?per_page=100"] = {"check_runs": [
            {"name": name, "conclusion": "success", "app": {"slug": "github-actions"}} for name in CI_NAMES]}
    for number, identifier in [(3, "01-C01"), (4, "01-I02")]:
        api.data[f"issues/{number}"] = {"number": number, "state": "closed", "state_reason": "completed",
            "body": f"<!-- plan-task:{identifier} -->\n"+block("task-evidence", {"pr": 200+number, "test_url": "https://example.test/test", "ci_run_id": 901})}
        api.data[f"pulls/{200+number}"] = {"merged": True, "base": {"ref": "game"}, "head": {"sha": "main0"},
            "merge_commit_sha": "main0", "body": identifier}
    api.data["actions/runs/950"] = {"head_sha": "main0", "status": "completed", "conclusion": "success", "path": ".github/workflows/issue-gate-audit.yml"}
    return Policy(api, plan, registry, state), api


def test_complete_phase_acceptance_requires_and_validates_evidence():
    policy, _ = policy_fixture()
    policy.gate("P01-GATE")
    assert ("P00-GATE", False) in policy.validated_gates
    assert ("P01-GATE", False) in policy.validated_gates


def test_closed_gate_with_reopened_required_task_fails():
    policy, api = policy_fixture()
    api.data["issues/3"]["state"] = "open"
    with pytest.raises(ValueError, match="not completed"):
        policy.gate("P01-GATE")


def test_checkbox_only_closed_gate_fails():
    policy, api = policy_fixture()
    api.data["issues/1"]["body"] = "<!-- plan-gate:P00-GATE -->\n- [x] Everything complete"
    with pytest.raises(ValueError, match="gate-evidence"):
        policy.gate("P00-GATE")


def test_ready_for_promotion_does_not_require_own_gate_or_final_task_closed():
    policy, api = policy_fixture()
    issue = api.data["issues/2"]
    evidence = declaration(issue["body"], "gate-evidence")
    evidence["status"] = "ready_for_promotion"
    issue["state"] = "open"
    issue["body"] = "<!-- plan-gate:P01-GATE -->\n" + block("gate-evidence", evidence)
    api.data["issues/4"]["state"] = "open"
    policy.gate("P01-GATE", ready=True)
    with pytest.raises(ValueError):
        policy.gate("P01-GATE")


def test_unaccepted_previous_gate_blocks_later_acceptance():
    policy, api = policy_fixture()
    api.data["issues/1"]["state"] = "open"
    with pytest.raises(ValueError, match="not closed"):
        policy.gate("P01-GATE")


@pytest.mark.parametrize("broken", ["ci", "checkpoint", "review"])
def test_invalid_release_evidence_cannot_accept_gate(broken):
    policy, api = policy_fixture()
    if broken == "ci":
        api.data["actions/runs/901"]["conclusion"] = "failure"
    elif broken == "checkpoint":
        api.data["git/ref/tags/checkpoint/00"]["object"]["sha"] = "unrelated"
    else:
        api.data["pulls/100/reviews"][0]["user"]["login"] = "author"
    with pytest.raises(ValueError):
        policy.gate("P00-GATE")


def test_unapproved_future_phase_fails_before_feature_work():
    policy, _ = policy_fixture()
    pr = {"head": {"ref": "feature/01-c01-contract"}}
    with pytest.raises(ValueError, match="not explicitly authorized"):
        policy.validate_pr(pr, {"classification": "planned", "phase": "01", "task_ids": ["01-C01"]}, ["src/smart_racing/core/graph.py"])
