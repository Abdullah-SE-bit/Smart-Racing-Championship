"""Create/resume roadmap issues and native dependencies; never close issues or gates."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time

from scripts.github_api import GitHub
from scripts.plan_backlog import parse_plan


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/development/issue_registry.json"
BEGIN, END = "<!-- coordination:begin -->", "<!-- coordination:end -->"
LABELS = (
    "critical parallel integration phase-gate blocked ready in-progress in-review "
    "needs-integration verified type:maintenance type:bug type:feature area:algorithms "
    "area:game area:ui area:testing area:docs area:infrastructure"
).split() + [f"phase:{i:02d}" for i in range(17)]


def identify(issue: dict) -> str | None:
    if "pull_request" in issue:
        return None
    marker = re.search(r"<!-- plan-(?:task|gate):([\w-]+) -->", issue.get("body") or "")
    if marker:
        return marker[1]
    title = re.match(r"\[P?(\d{2}-[CPI]\d{2})\]|\[(P\d{2}-GATE)\]", issue["title"])
    return next((v for v in title.groups() if v), None) if title else None


def merge_body(existing: str, managed: str) -> str:
    # Preserve verified checkbox records when refreshing generated metadata.
    checked = {line.replace("- [x] ", "- [ ] ", 1) for line in existing.splitlines() if line.startswith("- [x] ")}
    managed = "\n".join(line.replace("- [ ] ", "- [x] ", 1) if line in checked else line for line in managed.splitlines())
    block = BEGIN + "\n" + managed + "\n" + END
    if BEGIN in existing and END in existing:
        start, stop = existing.index(BEGIN), existing.index(END) + len(END)
        return existing[:start] + block + existing[stop:]
    return (existing.rstrip() + "\n\n" if existing else "") + block


def issue_link(identifier, registry):
    entry = registry.get(identifier)
    return f"[{identifier} (#{entry['number']})]({entry['url']})" if entry else f"`{identifier}` (link pending creation)"


def task_body(task, plan, registry):
    phase = plan["phases"][task["phase"]]
    dependencies = "\n".join("- " + issue_link(k, registry) for k in task["dependencies"])
    optional = "Optional enhancement: does NOT block P04 acceptance unless the user explicitly expands scope." if not task["required"] else "Required phase task."
    return f"""<!-- plan-task:{task['id']} -->
## Identification
- Stable plan ID: `{task['id']}`; phase P{task['phase']}; classification: {task['lane']}.
- Planned owner(s): {', '.join(task['owners'])} (role {'+'.join(task['roles'])}); joint responsibility is retained.
- Source: `implementation_plan.md`, task row at line {task['source_line']}, Phase {task['phase']}.
- {optional}
- State: BLOCKED / NOT_STARTED. Planned ownership is not an implementation claim or authorization.

## Objective
{task['title']}. This contributes to the phase's integrated runnable milestone below.

## Scope and observable acceptance from the plan
{task['scope']}

## Dependencies
{dependencies}

Previous gate acceptance, human phase authorization, a merged shared kickoff,
and a remotely published personal handoff claim are required before application work.

## Inputs and outputs
Use the exact data, contracts, fixtures and observable outputs described in the
scope above. Review upstream public interfaces before coding; record units,
invalid-input behavior and changes to consumers. Do not invent unspecified game rules.

## Acceptance criteria
- [ ] Deliver the task-row behavior and observable acceptance above.
- [ ] Prerequisite task PRs are merged and previous phase gate is accepted.
- [ ] Add relevant positive, negative, boundary and integration evidence.
- [ ] Preserve deterministic inputs/ties where applicable and shared gameplay/Lab implementations.
- [ ] Update public-contract documentation and personal handoff; integrate through the correct PR.
- [ ] Link actual tests, CI and demonstration evidence; no unsupported completion claims.

## Testing
- Positive: exercise the task's valid input and specified output/interaction.
- Negative: invalid/unavailable inputs or rejected states relevant to this task.
- Boundary: empty/minimal/limit inputs for algorithms/data, or navigation/exit/error paths for UI/tooling.
- Integration: prove the deliverable works with its listed producers/consumers.
- Determinism: repeat identical inputs, seeds and simulation ticks where applicable;
  record a reason if not applicable. For evidence/report-only tasks, validate links,
  reproducibility and consistency instead of inventing algorithm tests.

## Visible demonstration / phase milestone
{phase['deliverable']}

Task-specific scope above determines this task's contribution; backend tasks
need real phase integration, not an unrelated demonstration copy.

## Deliverables
The scoped implementation or documentation, relevant tests/fixtures, public
interface notes, personal handoff, and reproducible evidence required above.

## Pull request requirements
Use `feature/{task['id'].lower()}-<description>` from `game` or an explicitly
documented dependency branch. Link this issue; merge upstream contracts first.
Target `game` unless this is the phase's final promotion into `main`. Do not
close final promotion work before actual main integration/checkpoint evidence.
Main needs one eligible non-author approval; game has zero required reviews.

## Viva explanation
Explain why this task exists, its actual inputs/outputs, data structures,
correctness assumptions, complexity where applicable, edge cases, integration
point, tests and limitations using the implementation that is eventually merged.

## Source limitations
Project.pdf is unavailable in this checkout; the plan's historical statement
that it was reviewed is not verification by this setup task. No code is implemented by issue creation.
"""


def gate_body(identifier, plan, registry):
    number = identifier[1:3]
    if number == "00":
        return """<!-- plan-gate:P00-GATE -->
## Phase 00 infrastructure readiness — BLOCKED, not accepted
No historical task completion issues are invented. Verify actual infrastructure:
- [ ] Existing scaffold and remote game branch verified.
- [ ] Main approval and game no-review policy verified; applicable CI gates enforced.
- [ ] CI, PR and issue templates published; coordination AGENTS policies published.
- [ ] implementation_plan.md and central/personal handoffs published.
- [ ] All 171 task issues and 17 gates mapped in the registry without duplicates.
- [ ] Native dependency relationships audited, or exact API limitation and fallback recorded.
- [ ] Phase Gate Validation actually runs and is required where available.
- [ ] Issue-close audit is activated from the default branch and tested.
- [ ] Human review, accepted infrastructure promotion PR into main, stable commit/checkpoint and CI evidence recorded.

## Evidence and final approval
Attach real PRs, current CI run, main commit, checkpoint, review and handoff links.
Keep this gate OPEN until infrastructure is verified and accepted by a human.
No playable game or Phase 01 acceptance is implied. Phase 01 cannot begin yet.
Read docs/development/PHASE_GATE_POLICY.md for machine-readable acceptance evidence.
"""
    phase = plan["phases"][number]
    required = [key for key in phase["tasks"] if plan["tasks"][key]["required"]]
    tasks = "\n".join("- [ ] " + issue_link(key, registry) for key in required)
    optional = [key for key in phase["tasks"] if key not in required]
    optional_text = "\n".join("- Optional, not gate-blocking: " + issue_link(key, registry) for key in optional)
    critical = ", ".join(key for key in required if plan["tasks"][key]["lane"] == "critical")
    parallel = ", ".join(key for key in required if plan["tasks"][key]["lane"] == "parallel")
    integration = ", ".join(key for key in required if plan["tasks"][key]["lane"] == "integration")
    previous = issue_link(f"P{int(number)-1:02d}-GATE", registry)
    acceptance = "\n".join(phase["acceptance"])
    return f"""<!-- plan-gate:{identifier} -->
## Phase {number}: {phase['title']}
Status: BLOCKED / NOT_STARTED. Previous accepted gate required: {previous}.

## Runnable milestone and objective
{phase['deliverable']}

## Required task issues
{tasks}
{optional_text}

## Dependency graph and ordering
Previous gate -> this phase's tasks with their exact plan prerequisites -> integration
-> verification -> approved game-to-main promotion -> final integration issue closure
-> this gate accepted. Next-phase tasks are blocked by this gate. See each task's
native blocked-by relationships and docs/development/TASK_DEPENDENCIES.md.

## Critical path
{critical}. Preserve the explicit task DAG, not a blanket ordering of all C tasks.

## Parallel task status
{parallel}. All NOT_STARTED; preserve independence except the plan's explicit prerequisites.

## Integration requirements
{integration}. Merge all actual prerequisites, rerun regression and verify the real vertical slice.

## Plan-specific demonstration and acceptance
{acceptance}

## Required gate evidence
- [ ] Every required task issue completed with merged relevant PRs; no unchecked blockers.
- [ ] Automated positive/negative/boundary/integration/determinism tests and regression pass.
- [ ] Current applicable CI succeeds; attach exact revision and run URLs.
- [ ] Human manual GUI acceptance and runnable milestone demonstrated on real data.
- [ ] docs/demos/PHASE_{number}.md and PHASE_{number}_ACCEPTANCE.md record actual demo/test evidence.
- [ ] Required algorithm/rule/report documentation is accurate.
- [ ] Three personal handoffs are current; central mandoff.md reconciled by one writer.
- [ ] Ready-for-promotion evidence established WITHOUT requiring this gate already closed.
- [ ] Approved promotion PR merged into main; final integration task completed.
- [ ] Main commit and emergency checkpoint/tag or release recorded with truthful limitations.
- [ ] Human final approval verified; gate audit passes before closing this issue.

## State distinction
READY_FOR_PROMOTION permits this phase's final promotion while its final I task
remains open. ACCEPTED requires real main promotion and all required tasks closed.
Never require this gate to close before its own promotion PR; never start the
next phase before acceptance plus new human authorization.
"""


def write_registry(plan, registry, audit=None):
    data = {"schema_version": 1, "repo": "Abdullah-SE-bit/Smart-Racing-Championship",
            "plan_sha256": plan["plan_sha256"], "updated_at": datetime.now(timezone.utc).isoformat(),
            "issues": registry, "audit": audit or {"status": "IN_PROGRESS"}}
    temporary = REGISTRY.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temporary.replace(REGISTRY)
    lines = ["# GitHub issue registry", "", "Generated from implementation_plan.md; plan IDs are distinct from GitHub issue numbers.",
             "All implementation remains blocked until previous gate acceptance and explicit authorization.",
             "04-P05 is optional and does not block P04 (user-confirmed).", "",
             "| Plan ID | GitHub issue | Phase | Planned owner | Classification | Dependencies | Gate | Verified state |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for key, task in plan["tasks"].items():
        entry = registry.get(key)
        link = issue_link(key, registry)
        state = entry.get("state", "missing") if entry else "MISSING"
        lines.append(f"| {key} | {link} | P{task['phase']} | {', '.join(task['owners'])} | {task['lane']}{' (optional)' if not task['required'] else ''} | {', '.join(task['dependencies'])} | {issue_link('P'+task['phase']+'-GATE', registry)} | {state.upper()}; not implemented/accepted |")
    lines += ["", "## Phase gates", "", "| Gate | Issue | Required tasks | State |", "| --- | --- | --- | --- |"]
    for i in range(17):
        key = f"P{i:02d}-GATE"
        lines.append(f"| {key} | {issue_link(key, registry)} | {len(plan['dependencies'][key]) if i else 'Infrastructure evidence'} | OPEN / BLOCKED |")
    lines += ["", "## Assignment limitations", "", "Abdullah = Abdullah-SE-bit (verified). Taha = TahaSohail-Goat and Shaheer = Artfever",
              "were supplied by the user and their accounts verified, but neither is currently assignable.",
              "Their planned ownership is preserved in issue bodies; GitHub assignees remain unset.", "",
              "## Dependency audit", "", json.dumps(data["audit"], indent=2), ""]
    (ROOT / "docs/development/ISSUE_REGISTRY.md").write_text("\n".join(lines), encoding="utf-8")
    overview = ["# Task dependencies", "", "Authoritative task relationships are parsed from implementation_plan.md.",
                "Strict phase sequence: P00-GATE -> P01 -> P01-GATE -> ... -> P16 -> P16-GATE.",
                "No future implementation starts early. An open current gate does not block its own final promotion.",
                "04-P05 remains optional. Every required integration task remains a gate blocker.", ""]
    for number, phase in plan["phases"].items():
        overview += [f"## P{number}: {phase['title']}", "", f"Gate: {issue_link('P'+number+'-GATE', registry)}", "",
                     "| Task | Lane | Upstream blockers |", "| --- | --- | --- |"]
        for key in phase["tasks"]:
            task = plan["tasks"][key]
            overview.append(f"| {issue_link(key, registry)} | {task['lane']} | {'; '.join(issue_link(d, registry) for d in task['dependencies'])} |")
        overview += [""]
    (ROOT / "docs/development/TASK_DEPENDENCIES.md").write_text("\n".join(overview), encoding="utf-8")


def native_snapshot(api):
    """Read actual issue bodies and native edges in paginated GraphQL snapshots."""
    owner, name = api.repo.split("/")
    cursor, result = None, {}
    while True:
        query = '''query($owner:String!,$name:String!,$cursor:String){repository(owner:$owner,name:$name){
          issues(first:100,after:$cursor,states:[OPEN,CLOSED]){pageInfo{hasNextPage endCursor}
          nodes{id databaseId number title body state url blockedBy(first:100){nodes{number} pageInfo{hasNextPage}}}}}}'''
        response = api.request("POST", "/graphql", {"query": query, "variables": {"owner": owner, "name": name, "cursor": cursor}})
        if response.get("errors"):
            raise ValueError("GitHub dependency snapshot failed: " + json.dumps(response["errors"]))
        connection = response["data"]["repository"]["issues"]
        for issue in connection["nodes"]:
            if issue["blockedBy"]["pageInfo"]["hasNextPage"]:
                raise ValueError("More than 100 blockers requires explicit pagination before editing")
            key = identify(issue)
            if key:
                if key in result:
                    raise ValueError(f"Duplicate task ID in live snapshot: {key}")
                result[key] = issue
        if not connection["pageInfo"]["hasNextPage"]:
            return result
        cursor = connection["pageInfo"]["endCursor"]


def link_and_audit(api, plan, registry, mode):
    snapshot = native_snapshot(api)
    mutations = []
    for key, prerequisites in plan["dependencies"].items():
        issue = snapshot[key]
        body = task_body(plan["tasks"][key], plan, registry) if key in plan["tasks"] else gate_body(key, plan, registry)
        updated = merge_body(issue.get("body") or "", body)
        if mode == "link" and updated != issue.get("body"):
            mutations.append("updateIssue(input:{id:" + json.dumps(issue["id"]) + ",body:" + json.dumps(updated) + "}){issue{number}}")
        actual = {i["number"] for i in issue["blockedBy"]["nodes"]}
        for parent in prerequisites:
            if mode == "link" and registry[parent]["number"] not in actual:
                mutations.append("addBlockedBy(input:{issueId:" + json.dumps(issue["id"]) + ",blockingIssueId:" + json.dumps(snapshot[parent]["id"]) + "}){issue{number} blockingIssue{number}}")
    # GraphQL executes mutation fields serially. Keep batched HTTP requests well
    # below GitHub's documented content-request ceiling; the client also honors
    # secondary-limit responses. Resume from live state after partial responses.
    completed = 0
    for start in range(0, len(mutations), 15):
        batch = mutations[start:start+15]
        response = api.request("POST", "/graphql", {"query": "mutation{" + " ".join(f"m{i}:{value}" for i, value in enumerate(batch)) + "}"})
        if response.get("errors"):
            write_registry(plan, registry, {"status": "INCOMPLETE", "errors": response["errors"], "resume": "Rerun link; live snapshots recover partial success without duplicating edges."})
            raise ValueError("Native mutation failed; partial progress saved: " + json.dumps(response["errors"]))
        completed += len(batch)
        write_registry(plan, registry, {"status": "IN_PROGRESS", "logical_writes_applied": completed, "logical_writes_remaining": len(mutations)-completed})
        print(f"Applied {completed}/{len(mutations)} remaining body/native dependency updates", flush=True)
        time.sleep(2)
    actual = native_snapshot(api)
    errors, verified = [], 0
    for key, prerequisites in plan["dependencies"].items():
        numbers = {i["number"] for i in actual[key]["blockedBy"]["nodes"]}
        missing = [parent for parent in prerequisites if registry[parent]["number"] not in numbers]
        unexpected = numbers - {registry[parent]["number"] for parent in prerequisites}
        missing_links = [parent for parent in prerequisites if registry[parent]["url"] not in actual[key]["body"]]
        if missing or unexpected or missing_links:
            errors.append({"issue": key, "missing": missing, "unexpected": sorted(unexpected), "missing_body_links": missing_links})
        verified += len(prerequisites) - len(missing)
    audit = {"status": "VERIFIED" if not errors else "INCOMPLETE", "tasks": len(plan["tasks"]), "gates": 17,
             "expected_edges": sum(map(len, plan["dependencies"].values())), "edges_verified": verified,
             "duplicates": 0, "errors": errors, "unsupported": []}
    write_registry(plan, registry, audit)
    print(json.dumps(audit), flush=True)
    if errors:
        raise ValueError("Native dependency audit incomplete; see registry. No failures were silently skipped.")


def sync(mode: str):
    plan = parse_plan(ROOT / "implementation_plan.md")
    api = GitHub("Abdullah-SE-bit/Smart-Racing-Championship")
    repository = api.request("GET", "")
    if repository["full_name"] != api.repo or not repository["permissions"]["push"]:
        raise ValueError("Wrong repository or insufficient write permission")
    issues = api.pages("issues?state=all")
    indexed = {}
    for issue in issues:
        key = identify(issue)
        if key:
            if key in indexed:
                raise ValueError(f"Duplicate plan ID {key}: #{indexed[key]['number']} and #{issue['number']}")
            indexed[key] = issue
    registry = {key: {"number": value["number"], "id": value["id"], "url": value["html_url"], "state": value["state"]} for key, value in indexed.items()}
    created, reused = [], list(registry)
    if mode == "create":
        existing_labels = {label["name"] for label in api.pages("labels")}
        for label in LABELS:
            if label not in existing_labels:
                api.request("POST", "labels", {"name": label, "color": "5319e7" if label.startswith("phase:") else "1d76db", "description": "Coordination metadata; labels alone do not authorize work."})
        keys = list(plan["tasks"]) + [f"P{i:02d}-GATE" for i in range(17)]
        for key in keys:
            if key in registry:
                continue
            task = plan["tasks"].get(key)
            if task:
                title = f"[P{key}] {task['title']}"
                labels = ["phase:"+task["phase"], task["lane"], "blocked", "type:feature"]
                labels += ["area:algorithms" if "A" in task["roles"] else "area:game" if "B" in task["roles"] else "area:ui"]
                managed = task_body(task, plan, registry)
                assignees = ["Abdullah-SE-bit"] if "A" in task["roles"] else []
            else:
                title = f"[{key}] " + ("Repository and Development Infrastructure Ready" if key == "P00-GATE" else "Phase " + key[1:3] + " acceptance")
                labels = ["phase:"+key[1:3], "phase-gate", "blocked", "area:infrastructure" if key == "P00-GATE" else "integration"]
                managed, assignees = gate_body(key, plan, registry), []
            issue = api.request("POST", "issues", {"title": title, "body": merge_body("", managed), "labels": labels, "assignees": assignees})
            registry[key] = {"number": issue["number"], "id": issue["id"], "url": issue["html_url"], "state": issue["state"]}
            created.append(key)
            write_registry(plan, registry)
            print(f"Created {key}: #{issue['number']} ({len(registry)}/188)", flush=True)
        print(f"Creation complete: {len(created)} created, {len(reused)} reused.", flush=True)
    else:
        expected = set(plan["dependencies"])
        if expected != set(registry):
            raise ValueError(f"Registry coverage mismatch; missing={expected-set(registry)}, unexpected={set(registry)-expected}")
        link_and_audit(api, plan, registry, mode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["create", "link", "audit"])
    sync(parser.parse_args().mode)
