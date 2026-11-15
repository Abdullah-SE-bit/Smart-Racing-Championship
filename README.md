# Smart Racing Championship

**Scaffolding Only — Not Yet Implemented**

Smart Racing Championship is a planned 2D top-down racing game for the Design and
Analysis of Algorithms course. This repository currently contains only package
directories, development infrastructure, configuration, and documentation.
**No playable game exists yet.**
There is no application entry point or game command in this phase.

The planned stack is Python 3.12+, Pygame, JSON data files, pytest, Matplotlib,
Git/GitHub, and optional PyInstaller executable packaging. Python 3.12 is the
baseline development version recorded in `.python-version`.

## Planned scope

- Three circuits, each with at least ten mandatory checkpoints and two shortcuts.
- One human racer and three deterministic computer opponents.
- Five required GUI screens and twelve mandatory algorithm families.
- Dynamic road events, route recalculation, fuel, and nitro management.
- Championship scoring, rankings, and leaderboards.
- An Algorithm Lab using the exact algorithm implementations used by gameplay.
- Five reproducible experimental algorithm studies, automated tests, and reports.

The original assignment `Project.pdf` is absent and has **not been verified**.
This scaffold follows the supplied Phase 0 requirements. Exact algorithm lists,
screen definitions, experiment specifications, and game rules must be checked
against the PDF before implementation. No requirements have been invented to
fill those gaps.

## Windows setup (PowerShell)

Install Python 3.12 with the Windows Python launcher, then run these commands
from the existing repository directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

These commands use the virtual environment directly; activation is optional.
`requirements.txt` installs the project in editable mode with its runtime and
development dependencies, as declared in `pyproject.toml`. An equivalent install
is `python -m pip install -e ".[dev]"` using the virtual environment's Python.

For future executable packaging, install the optional packaging tools:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[packaging]"
```

No dependencies need to be installed to inspect this scaffold. Development
dependencies include Ruff for static analysis and PyYAML for infrastructure
configuration validation. Application tests will be added with functionality.
Infrastructure tests validate CI behavior without claiming game correctness.
Run `.\.venv\Scripts\python.exe -m pytest` to execute discovered tests, or
`.\.venv\Scripts\python.exe scripts/run_tests.py` for the CI feature-gate report.
Dependency ranges describe compatibility constraints, not a locked environment.
Future experimental submissions must record exact versions, inputs, and seeds.

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for package boundaries and
[AGENTS.md](AGENTS.md) for repository contribution instructions. Later phases
require explicit user instructions.

Development uses feature branches into `game`, then an integration PR into
`main`. Only `main` requires teammate approval; review is optional for `game`.
See [the workflow](docs/development/WORKFLOW.md),
[CI policy](docs/development/CI_POLICY.md), and
[verified governance status](docs/development/GOVERNANCE_STATUS.md).
