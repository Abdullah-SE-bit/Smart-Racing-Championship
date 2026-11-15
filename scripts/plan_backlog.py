"""Parse the supplied roadmap without renumbering or implementing its tasks."""

import hashlib
import re
from pathlib import Path


OWNERS = {"A": "Abdullah", "B": "Taha", "C": "Shaheer"}
LANES = {"C": "critical", "P": "parallel", "I": "integration"}
TASK_ROW = re.compile(r"^\| \*\*(\d{2}-[CPI]\d{2})\*\* \| (.*?) \| (.*?) \| (.*?) \|$")


def expand_dependencies(text: str) -> list[str]:
    expanded = re.sub(
        r"(\d{2}-[CPI])(\d{2})\.\.(\d{2})",
        lambda m: ", ".join(f"{m[1]}{i:02d}" for i in range(int(m[2]), int(m[3]) + 1)),
        text,
    )
    return list(dict.fromkeys(re.findall(r"\b\d{2}-[CPI]\d{2}\b", expanded)))


def validate_dag(nodes: dict[str, list[str]]) -> None:
    visiting, visited = set(), set()

    def visit(key):
        if key not in nodes:
            raise ValueError(f"Unknown dependency: {key}")
        if key in visiting:
            raise ValueError(f"Circular dependency involving {key}")
        if key in visited:
            return
        visiting.add(key)
        for parent in nodes[key]:
            visit(parent)
        visiting.remove(key)
        visited.add(key)

    for key in nodes:
        visit(key)


def parse_plan(path: Path) -> dict:
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    phases, tasks = {}, {}
    phase = None
    for line_number, line in enumerate(text.splitlines(), 1):
        heading = re.match(r"### PHASE (\d{2}) — (.+)", line)
        if heading:
            phase = heading[1]
            phases[phase] = {"title": heading[2], "tasks": [], "deliverable": "", "acceptance": []}
        if phase and line.startswith("**Deliverable:**"):
            phases[phase]["deliverable"] = line.removeprefix("**Deliverable:**").strip()
        if phase and line.startswith(("**Must pass:**", "**Show:", "**Show the examiner:", "**Evidence:", "**Phase exit:", "**Bonus criterion")):
            phases[phase]["acceptance"].append(line)
        row = TASK_ROW.match(line)
        if row:
            identifier, allocation, depends, scope = row.groups()
            if identifier in tasks or identifier[:2] != phase:
                raise ValueError(f"Duplicate or misplaced task: {identifier}")
            lane, roles = [s.strip() for s in allocation.split(" / ")]
            if lane != identifier[3] or any(r not in OWNERS for r in roles.split("+")):
                raise ValueError(f"Invalid owner or lane: {identifier}")
            plain = re.sub(r"[*`]", "", scope)
            title = plain.split(";")[0].rstrip(".")
            if len(title) > 220:
                title = title[:217].rsplit(" ", 1)[0] + "..."
            dependencies = expand_dependencies(depends)
            previous_gate = f"P{int(phase)-1:02d}-GATE"
            tasks[identifier] = {
                "id": identifier, "phase": phase, "lane": LANES[lane],
                "roles": roles.split("+"), "owners": [OWNERS[r] for r in roles.split("+")],
                "title": title, "scope": scope, "depends_source": depends,
                "dependencies": dependencies + [previous_gate], "source_line": line_number,
                "required": identifier != "04-P05",
            }
            phases[phase]["tasks"].append(identifier)
    if set(phases) != {f"{i:02d}" for i in range(1, 17)} or not tasks:
        raise ValueError("The complete 16-phase task backlog is required")
    nodes = {key: value["dependencies"] for key, value in tasks.items()}
    nodes["P00-GATE"] = []
    for number, data in phases.items():
        nodes[f"P{number}-GATE"] = [key for key in data["tasks"] if tasks[key]["required"]]
    validate_dag(nodes)
    normalized = text.replace("\r\n", "\n").encode("utf-8")
    return {"schema_version": 1, "plan_sha256": hashlib.sha256(normalized).hexdigest(), "phases": phases, "tasks": tasks, "dependencies": nodes}
