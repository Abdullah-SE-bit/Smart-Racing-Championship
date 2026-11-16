# Smart Racing Championship

A planned 2D top-down racing game for a Design and Analysis of Algorithms
course. Players plan routes, manage fuel and nitro, and respond to changing
roads while racing deterministic opponents. The project combines a polished,
animated Pygame interface with algorithms that have real roles in gameplay.

**Current status: implementation in progress.** A playable prototype, initial
algorithms, circuits, and tests are being built; the complete assignment and
bonus work are not yet finished.

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

Launch the current prototype with:

```powershell
.\.venv\Scripts\python.exe -m smart_racing
```

Use the mouse to navigate. In a race, select a road with the left/right arrow
keys, press Enter to drive, press N for nitro, and press F at a fuel station to
refuel. Space pauses the simulation. The race HUD reports recent resource and
race events and marks unavailable services on the map. Championship mode opens the planner before
each race in the fixed three-circuit season; results carry forward between races.
The planner can compare presets with an animated reveal of each computed route, switch to
an ordered checkpoint plan, generate a seeded circuit, show an invalid candidate,
inspect bounded endpoint alternatives, and save a circuit for later selection.
The circuit workshop shows the seed and the actual checkpoint, service, backbone,
road, obstacle and validation stages; it can also demonstrate a rejected track.
Generated circuits are available for quick races. Saved circuits are stored in
`%USERPROFILE%\SmartRacingChampionship\circuits`.
The window can be resized. Tab and Shift+Tab move between buttons and Enter
activates the focused button. In the planner, arrow keys change the destination;
hold Shift with an arrow key to change the starting vertex.
The Algorithm Lab uses the selected track and, when available, current
championship standings for its shared-algorithm demonstrations.
Windows CI also renders screen previews as the `interface-previews` workflow
artifact. To regenerate them locally, run
`.\.venv\Scripts\python.exe scripts/capture_previews.py`; the images are written
to `output/previews/`.
CI also builds the Windows executable and runs its headless smoke test before
and after extraction from a temporary test archive on a clean Windows runner.
Run the current automated tests with `.\.venv\Scripts\python.exe -m pytest`.

To build a Windows executable after installing the optional packaging tools, run
`powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1`. The output is
`dist/SmartRacingChampionship.exe` and
contains the circuit data. Build outputs are generated locally and Git-ignored.

To regenerate the current draft report, install `.[report]` and run
`.\.venv\Scripts\python.exe scripts/build_report.py`. The reproducible studies
are run with `.\.venv\Scripts\python.exe experiments/benchmarks/run_studies.py`;
raw results and an analysis are written under `experiments/results/`.

`scripts/package_submission.py` can later prepare a local ZIP once the actual
registration numbers and section are known. It does not upload or submit it.

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
The [demo and viva guide](docs/demo-and-viva.md) provides a rehearsal checklist
and prompts for explaining the implementation.
