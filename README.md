# Smart Racing Championship

A planned 2D top-down racing game for a Design and Analysis of Algorithms
course. Players plan routes, manage fuel and nitro, and respond to changing
roads while racing deterministic opponents. The project combines a polished,
animated Pygame interface with algorithms that have real roles in gameplay.

**Current status: Phase 0 scaffolding.** There is no playable application or
startup command yet. Source packages, supporting directories, configuration,
documentation, and the initial GitHub workflow are in place. Implementation
begins only when explicitly requested.

## Project scope

- Three distinct circuits, each with at least ten ordered checkpoints and two
  shortcuts, plus intersections, alternative routes, a cycle, and a dead end.
- One player and at least three deterministic opponents; multiple laps, fuel,
  nitro, road events, route recalculation, results, and championship standings.
- Five accessible screens: Main Menu, Track Explorer / Route Planner, Racing,
  Algorithm Lab, and Championship Dashboard. Animations should communicate real
  race and algorithm state while keeping the engine independent of rendering.
- All twelve required algorithm families: BFS, DFS, Dijkstra, A*, dynamic
  programming, greedy selection, backtracking, Prim or Kruskal, a heap/priority
  queue, Merge Sort, Quick Sort, and Heap Sort. Gameplay, the Lab, and experiments
  share the same implementations.
- All three advanced challenges: playable generated circuits, multi-objective
  route presets, and live top-k championship analytics.
- Five reproducible studies, meaningful tests, a technical report, executable
  submission, demo, and viva preparation.

The authoritative details, examples, formulas, and submission requirements are
in [the assignment transcription](docs/assignment-specification.md); use the
original PDF to resolve any transcription ambiguity. See the
[development workflow](docs/development-workflow.md) for a detailed delivery map.

## Planned technology

Python 3.12+, Pygame, JSON, pytest and Matplotlib; PyInstaller is available as
an optional packaging dependency. See [pyproject.toml](pyproject.toml) for the
declared version ranges. Record exact versions and experiment environments when
results are produced.

## Setup on Windows

From the repository directory in PowerShell, with Python 3.12 installed:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The requirements file installs the project in editable mode with its development
dependencies. To add the optional packaging tools later:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[packaging]"
```

There is no game command yet. Once real tests have been added, run them with
`.\.venv\Scripts\python.exe -m pytest`. An empty collection does not mean the
game has passed testing. No installation is required to browse the scaffold.

## Repository guide

| Location | Purpose |
| --- | --- |
| `src/smart_racing/` | Planned algorithms, game logic, data models, and UI. |
| `assets/`, `data/` | Versioned presentation assets, circuits, and configuration. |
| `tests/` | Unit, integration, and fixture locations for future tests. |
| `experiments/` | Benchmark drivers, datasets, and real results. |
| `docs/` | Assignment, architecture, algorithm, testing, and report material. |
| `.github/` | Contribution guidance, issue/PR templates, and CI workflow. |

Read [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for the full package map,
[AGENTS.md](AGENTS.md) for agent instructions, and
[CONTRIBUTING.md](.github/CONTRIBUTING.md) for the GitHub workflow. Issues can
be split or combined as needed; they track the project and do not impose phase
gates. Record important architecture and rule choices in `docs/architecture/`.
