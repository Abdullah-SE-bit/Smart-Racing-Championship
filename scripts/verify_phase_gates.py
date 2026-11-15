"""Read-only PR phase validation and evidence audit; no issue state is mutated."""

import argparse
import json
import os
from pathlib import Path
import re

from scripts.github_api import GitHub, GitHubError
from scripts.plan_backlog import parse_plan


ROOT = Path(__file__).resolve().parents[1]
CI_NAMES = {"Repository Validation", "Python Quality", "Automated Tests", "Integration Validation"}
MAINTENANCE_PREFIXES = ("maintenance/", "fix/", "docs/", "ci/", "refactor/", "hotfix/")
INFRA_ROOT_FILES = {"AGENTS.md", "README.md", "PROJECT_STRUCTURE.md", "implementation_plan.md", "mandoff.md", "pyproject.toml", "requirements.txt", ".gitignore", ".gitattributes", ".python-version"}


def declaration(body: str, marker="phase-governance") -> dict:
    matches = re.findall(r"<!-- " + re.escape(marker) + r" -->\s*```json\s*(.*?)\s*```", body or "", re.S)
    if len(matches) != 1:
        raise ValueError(f"Exactly one <!-- {marker} --> JSON declaration is required")
    value = json.loads(matches[0])
    if not isinstance(value, dict):
        raise ValueError("Declaration must be a JSON object")
    return value


def infrastructure_only(files: list[str]) -> bool:
    return bool(files) and all(
        name in INFRA_ROOT_FILES or name.startswith(("docs/", ".github/", "scripts/", "tests/"))
        for name in files
    )


def require_text(value, field):
    if not isinstance(value, str) or not value.strip() or value.lower().strip() in {"todo", "...", "tbd", "pending"}:
        raise ValueError(f"Missing meaningful {field}")


def validate_maintenance(meta: dict, branch: str, files: list[str], trusted: bool):
    if not branch.startswith(MAINTENANCE_PREFIXES):
        raise ValueError("Off-plan work needs a documented maintenance/fix/docs/ci/refactor/hotfix branch")
    for key in ("reason", "risks", "tests", "interfaces", "affected_gate"):
        require_text(meta.get(key), key)
    if meta.get("phase") is not None or meta.get("task_ids") != []:
        raise ValueError("Maintenance must not claim a fake phase task")
    if not trusted and not infrastructure_only(files):
        raise ValueError("Bootstrap exception permits infrastructure-only paths, never application files")
    if not infrastructure_only(files) and not meta.get("maintenance_comment_id"):
        raise ValueError("Application maintenance needs explicit human authorization bound to this revision")


class Policy:
    def __init__(self, api, plan: dict, registry: dict, state: dict):
        self.api, self.plan, self.registry, self.state = api, plan, registry, state
        self.cache = {}
        self.validated_gates = set()

    def get(self, path):
        if path not in self.cache:
            self.cache[path] = self.api.request("GET", path)
        return self.cache[path]

    def issue(self, identifier):
        if identifier not in self.registry:
            raise ValueError(f"No real GitHub issue registered for {identifier}")
        issue = self.get(f"issues/{self.registry[identifier]['number']}")
        marker = f"<!-- plan-{'gate' if identifier.endswith('GATE') else 'task'}:{identifier} -->"
        if marker not in (issue.get("body") or ""):
            raise ValueError(f"Issue identity mismatch: {identifier}")
        return issue

    def approved_pr(self, pr):
        reviews = self.api.pages(f"pulls/{pr['number']}/reviews")
        latest = {}
        for review in reviews:
            if review["state"] in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
                latest[review["user"]["login"]] = review
        return any(
            review["state"] == "APPROVED" and login != pr["user"]["login"]
            and review["user"]["type"] == "User"
            and review.get("author_association") in {"OWNER", "MEMBER", "COLLABORATOR"}
            and review.get("commit_id") == pr["head"]["sha"]
            for login, review in latest.items()
        )

    def successful_run(self, run_id, allowed_shas):
        run = self.get(f"actions/runs/{int(run_id)}")
        if run["status"] != "completed" or run["conclusion"] != "success" or run["head_sha"] not in allowed_shas:
            raise ValueError("CI evidence must be a successful run for the cited revision")
        checks = self.get(f"commits/{run['head_sha']}/check-runs?per_page=100")["check_runs"]
        good = {c["name"] for c in checks if c["conclusion"] == "success" and c["app"]["slug"] == "github-actions"}
        if not CI_NAMES <= good:
            raise ValueError("All four actual CI jobs must succeed on the cited revision")

    def task_complete(self, identifier):
        issue = self.issue(identifier)
        if issue["state"] != "closed" or issue.get("state_reason") != "completed":
            raise ValueError(f"Required task {identifier} is not completed")
        evidence = declaration(issue["body"], "task-evidence")
        pr = self.get(f"pulls/{int(evidence['pr'])}")
        if not pr["merged"] or pr["base"]["ref"] not in {"game", "main"}:
            raise ValueError(f"Task {identifier} needs a merged integration PR")
        if identifier not in (pr.get("body") or ""):
            raise ValueError(f"Merged PR does not identify task {identifier}")
        require_text(evidence.get("test_url"), "task test evidence URL")
        self.successful_run(evidence["ci_run_id"], {pr["head"]["sha"], pr["merge_commit_sha"]})

    def human_comment(self, comment_id, marker):
        comment = self.get(f"issues/comments/{int(comment_id)}")
        if comment["user"]["type"] != "User" or comment.get("author_association") not in {"OWNER", "MEMBER", "COLLABORATOR"}:
            raise ValueError("Approval/authorization must come from an eligible human account")
        if marker not in comment["body"]:
            raise ValueError(f"Approval comment must contain {marker}")

    def gate(self, identifier, ready=False):
        if (identifier, ready) in self.validated_gates:
            return
        issue = self.issue(identifier)
        evidence = declaration(issue["body"], "gate-evidence")
        expected = "ready_for_promotion" if ready else "accepted"
        if evidence.get("status") != expected:
            raise ValueError(f"{identifier} needs {expected} evidence")
        if not ready and (issue["state"] != "closed" or issue.get("state_reason") != "completed"):
            raise ValueError(f"{identifier} is not closed as completed")
        phase = identifier[1:3]
        if phase != "00":
            self.gate(f"P{int(phase)-1:02d}-GATE")
        required = self.plan["dependencies"][identifier]
        final_tasks = self.plan["phases"].get(phase, {}).get("tasks", [])[-1:]
        for task in required:
            if not (ready and task in final_tasks):
                self.task_complete(task)
        for key in ("demo_url", "test_url", "handoff_commit", "acceptance_document"):
            require_text(evidence.get(key), key)
        if ready:
            self.successful_run(evidence["ci_run_id"], {evidence["handoff_commit"]})
            self.api.file(evidence["acceptance_document"], evidence["handoff_commit"])
            self.validated_gates.add((identifier, ready))
            return
        promotion = self.get(f"pulls/{int(evidence['promotion_pr'])}")
        commit = evidence["main_commit"]
        if not promotion["merged"] or promotion["base"]["ref"] != "main" or promotion["merge_commit_sha"] != commit:
            raise ValueError("Accepted gate needs its actual merged main promotion commit")
        if phase != "00" and promotion["head"].get("ref") != "game":
            raise ValueError("Functional phases must be promoted from game")
        if not self.approved_pr(promotion):
            raise ValueError("Main promotion needs eligible non-author approval of its final revision")
        comparison = self.get(f"compare/{commit}...main")
        if comparison["behind_by"] != 0:
            raise ValueError("Accepted commit is not an ancestor of current main")
        ref = evidence.get("checkpoint_ref", "")
        if not ref.startswith("refs/tags/"):
            raise ValueError("Checkpoint must be a real stable tag reference")
        tag = self.get("git/ref/" + ref.removeprefix("refs/"))["object"]
        for _ in range(5):
            if tag["type"] != "tag":
                break
            tag = self.get("git/tags/" + tag["sha"])["object"]
        if tag["sha"] != commit:
            raise ValueError("Checkpoint tag does not resolve to the accepted main commit")
        self.human_comment(evidence["approval_comment_id"], f"gate-approved:{identifier}:{commit}")
        self.successful_run(evidence["ci_run_id"], {commit, promotion["head"]["sha"]})
        if phase == "00":
            for path in ("implementation_plan.md", "docs/development/issue_registry.json", ".github/workflows/phase-gates.yml", ".github/workflows/issue-gate-audit.yml"):
                self.api.file(path, commit)
            audit_run = self.get(f"actions/runs/{int(evidence['audit_run_id'])}")
            if audit_run["status"] != "completed" or audit_run["conclusion"] != "success" or audit_run["head_sha"] != commit or audit_run.get("path") != ".github/workflows/issue-gate-audit.yml":
                raise ValueError("P00 needs a real successful default-branch issue-audit run")
        handoff = evidence["handoff_commit"]
        if self.get(f"compare/{handoff}...{commit}")["behind_by"] != 0:
            raise ValueError("Handoff commit is not integrated into accepted main")
        for path in ["mandoff.md", evidence["acceptance_document"], *[m["handoff"] for m in self.state["members"].values()]]:
            self.api.file(path, commit)
        self.validated_gates.add((identifier, ready))

    def authorized(self, phase):
        if self.state.get("authorized_phase") != phase:
            raise ValueError(f"Phase {phase} is not explicitly authorized in trusted base policy")
        self.human_comment(self.state["authorization_comment_id"], f"phase-authorized:P{phase}")

    def kickoff(self, phase):
        kickoff = self.state.get("kickoff")
        if not kickoff or kickoff.get("phase") != phase:
            raise ValueError("No published kickoff for this phase")
        pr = self.get(f"pulls/{int(kickoff['pr'])}")
        if not pr["merged"] or pr["base"]["ref"] != "game" or not self.approved_pr(pr):
            raise ValueError("Kickoff must be merged into game with teammate approval")
        self.api.file("mandoff.md", pr["merge_commit_sha"])

    def validate_pr(self, pr: dict, meta: dict, files: list[str]):
        kind = meta.get("classification")
        branch = pr["head"]["ref"]
        if kind == "maintenance":
            validate_maintenance(meta, branch, files, trusted=True)
            if not infrastructure_only(files):
                self.human_comment(meta["maintenance_comment_id"], f"maintenance-approved:#{pr['number']}:{pr['head']['sha']}")
                for filename in files:
                    if filename.startswith(("src/", "data/", "assets/")):
                        self.api.file(filename, "main")
            return
        if kind not in {"planned", "integration", "promotion", "kickoff"}:
            raise ValueError("Unknown work classification")
        phase = str(meta.get("phase", ""))
        if phase not in self.plan["phases"]:
            raise ValueError("An exact phase 01..16 is required")
        self.authorized(phase)
        self.gate(f"P{int(phase)-1:02d}-GATE")
        if kind == "kickoff":
            if branch != f"docs/kickoff-p{phase}" or not files or not all(p.endswith((".md", ".json")) and (p.startswith("docs/") or p == "mandoff.md") for p in files):
                raise ValueError("Kickoff needs its dedicated docs-only branch")
            if not self.approved_pr(pr):
                raise ValueError("Kickoff-specific teammate approval is pending")
            return
        self.kickoff(phase)
        if kind == "promotion":
            if branch != "game" or pr["base"]["ref"] != "main":
                raise ValueError("Phase promotion must be game -> main")
            self.gate(f"P{phase}-GATE", ready=True)
            return
        ids = meta.get("task_ids")
        if not isinstance(ids, list) or not ids:
            raise ValueError("Feature work must link at least one real task issue")
        for identifier in ids:
            task = self.plan["tasks"].get(identifier)
            if not task or task["phase"] != phase or identifier not in self.state.get("authorized_task_ids", []):
                raise ValueError(f"Task {identifier} is unknown, mismatched or unauthorized")
            issue = self.issue(identifier)
            linked = re.search(r"(?:#|/issues/)" + str(issue["number"]) + r"\b", pr.get("body") or "")
            if issue["state"] != "open" or not linked:
                raise ValueError("Task must be open and linked by actual issue number in the PR")
            if identifier == ids[0] and not re.match(r"feature/p?" + re.escape(identifier.lower()) + r"(?:-|$)", branch):
                raise ValueError("Feature branch must identify its leading exact plan task")
            native = {i["number"] for i in self.api.pages(f"issues/{issue['number']}/dependencies/blocked_by")}
            for dependency in task["dependencies"]:
                if self.registry[dependency]["number"] not in native:
                    raise ValueError(f"Missing native dependency {identifier} <- {dependency}")
                if not dependency.endswith("GATE"):
                    self.task_complete(dependency)
            claim = self.state.get("claims", {}).get(identifier)
            if not claim or claim.get("branch") != branch or claim.get("owner") not in task["owners"]:
                raise ValueError("No serialized kickoff allocation / branch claim for task")
            member = self.state["members"][claim["owner"]]
            if pr["user"]["login"] != member["login"]:
                raise ValueError("PR author does not match the documented branch claimant")
            handoff_commit = meta.get("handoff_commit") or claim.get("handoff_commit")
            require_text(handoff_commit, "remote personal handoff commit")
            handoff = self.get(f"commits/{handoff_commit}")
            if {f["filename"] for f in handoff["files"]} != {member["handoff"]}:
                raise ValueError("Personal claim must be a separate handoff-only commit")
            if self.get(f"compare/{handoff_commit}...{pr['head']['sha']}")["behind_by"] != 0:
                raise ValueError("Remote personal handoff is not an ancestor of this PR")
            if identifier not in self.api.file(member["handoff"], handoff_commit):
                raise ValueError("Published handoff does not identify the task")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--event", default=os.environ.get("GITHUB_EVENT_PATH"))
    args = parser.parse_args()
    repo = os.environ.get("GITHUB_REPOSITORY", "Abdullah-SE-bit/Smart-Racing-Championship")
    api = GitHub(repo)
    event = json.loads(Path(args.event).read_text(encoding="utf-8")) if args.event else {}
    if args.audit:
        registry = json.loads((ROOT / "docs/development/issue_registry.json").read_text())
        state = json.loads((ROOT / "docs/development/phase_state.json").read_text())
        policy = Policy(api, parse_plan(ROOT / "implementation_plan.md"), registry["issues"], state)
        failures = []
        audited = 0
        for i in range(17):
            key = f"P{i:02d}-GATE"
            if policy.issue(key)["state"] == "closed":
                audited += 1
                try:
                    policy.gate(key)
                except (ValueError, KeyError, GitHubError) as error:
                    failures.append(f"{key}: {error}")
        if failures:
            raise ValueError("Premature/invalid gate closure; human correction required:\n" + "\n".join(failures))
        print(f"Audited {audited} closed gates; no invalid acceptance found. Open gates remain unaccepted.")
        return
    if "pull_request" not in event:
        raise ValueError("A real pull request event is required")
    pr = api.request("GET", f"pulls/{event['pull_request']['number']}")
    if pr["base"]["ref"] not in {"game", "main"} and not pr["base"]["ref"].startswith("feature/"):
        raise ValueError("Unsupported target branch")
    files = [f["filename"] for f in api.pages(f"pulls/{pr['number']}/files")]
    meta = declaration(pr.get("body") or "")
    base = pr["base"]["sha"]
    try:
        state = json.loads(api.file("docs/development/phase_state.json", base))
        registry = json.loads(api.file("docs/development/issue_registry.json", base))
    except GitHubError as error:
        if error.status != 404 or meta.get("classification") != "maintenance":
            raise
        validate_maintenance(meta, pr["head"]["ref"], files, trusted=False)
        print("Validated infrastructure-only bootstrap exception. No phase is authorized or accepted.")
        return
    # Use the target revision's roadmap as well as its authorization state.
    import tempfile

    with tempfile.TemporaryDirectory(prefix="smart-racing-policy-") as folder:
        path = Path(folder) / "implementation_plan.md"
        path.write_text(api.file("implementation_plan.md", base), encoding="utf-8")
        plan = parse_plan(path)
    Policy(api, plan, registry["issues"], state).validate_pr(pr, meta, files)
    print("Phase Gate Validation passed for declared scope; no additional phase is authorized.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, GitHubError) as error:
        raise SystemExit(f"Phase gate validation FAILED: {error}") from error
