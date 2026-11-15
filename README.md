# Smart Racing Championship

**Scaffolding Only — Not Yet Implemented**

Smart Racing Championship is a planned 2D top-down racing game for the Design and
Analysis of Algorithms course. This repository currently contains only package
directories, configuration, and documentation. **No playable game exists yet.**
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

The complete assignment specification has been transcribed to
[docs/assignment-specification.md](docs/assignment-specification.md) and verified
against the supplied `Project.pdf`. Consult it before implementation; this
repository remains at Phase 0 scaffolding only.

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

No dependencies need to be installed to inspect this scaffold. Tests will be
added with functionality in later phases. Once tests exist, run them with
`.\.venv\Scripts\python.exe -m pytest`; currently pytest has no tests to collect.
Dependency ranges describe compatibility constraints, not a locked environment.
Future experimental submissions must record exact versions, inputs, and seeds.

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for package boundaries and
[AGENTS.md](AGENTS.md) for repository contribution instructions. Later phases
require explicit user instructions.

See [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) for the lightweight
issue, branch, and pull request workflow.
