<div align="center">

[![Python checks](https://github.com/TahaSohail-Goat/Smart-Racing-Championship/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/TahaSohail-Goat/Smart-Racing-Championship/actions/workflows/ci.yml)

# REDLINE

### SMART RACING CHAMPIONSHIP

**Choose the line. Manage the risk. Take the title.**

![REDLINE — race night](assets/images/pit-lane-night.png)

*A strategy racing game where route algorithms, resource decisions, and changing track conditions shape every race.*

</div>

---

## On the grid

REDLINE is a Windows-first, keyboard-and-mouse racing game built with Python
and Pygame for a Design and Analysis of Algorithms project. Read the circuit,
choose a route, manage fuel and nitro, and race three deterministic rivals.
Then see the algorithms behind those decisions in the Algorithm Lab and follow
the standings through a three-circuit championship.

The game combines a restrained motorsport broadcast look with real algorithm
work. The 3D-style camera is a projection of the track graph; the tactical map,
route planner, race engine, Lab, and experiments all use the same circuit data
and shared algorithm implementations.

> **Project status:** The playable game, required algorithms, three bonus
> challenges, automated tests, studies, and Windows build workflow are in place.
> Release preparation remains: the report needs group details, and a human
> playthrough, final named ZIP, demo, and viva are still ahead. See the
> [assignment-wide QA checklist](docs/testing/assignment-requirements-audit.md)
> for evidence and open items.

## The race weekend

| Session | What you do |
|---|---|
| **Main Menu** | Choose a championship, quick race, or Algorithm Lab; select a circuit and adjust controls, sound, and motion. |
| **Track Explorer** | Inspect the road graph, select endpoints, compare balanced, speed, economy, and safety routes, and review fuel recommendations. |
| **Quick Race** | Drive through ordered checkpoints, choose legal roads, manage fuel and nitro, and react to timed road events. |
| **Algorithm Lab** | Step, play, pause, and reset real BFS, routing, resource, event, generation, sorting, and top-k traces. |
| **Championship** | Race all three venues, review results, watch points update, and follow the live top-k standings to the finale. |

Circuits contain ten mandatory checkpoints, shortcuts, alternate roads,
services, obstacles, and dynamic conditions. The race engine runs at a fixed
simulation step; rendering and screen animation do not decide race outcomes.

## Motion with a purpose

The interface takes cues from a live race broadcast: graphite panels, clean
typography, trackside photography, timing data, and a controlled pit-red accent.
Motion calls attention to game state and reinforces a transition instead of
running as decoration:

- **Launch:** a four-second starting-light intro can be skipped immediately.
- **Quick Race:** the grid countdown holds the simulation until lights out.
- **Championship:** venue openers set the scene; classification and standings
  animate the points change between rounds and reveal the winner at the finale.
- **Route Planner:** selected routes reveal along the actual graph; comparisons
  use computed paths and costs.
- **Race:** the projected broadcast camera follows live racer positions, while
  the tactical camera shows the same race from above.
- **Algorithm Lab:** graph frontiers, heap changes, sort movements, and resource
  tables animate from recorded algorithm steps.

The pit-lane car image is the still main-menu backdrop. Venue scenes follow the
selected circuit in the game and circuit preview. Reduced Motion is saved in
player preferences and removes timed presentation movement while keeping the
screens and controls usable.

## Get on track

### Windows quick start

Install Python 3.12, open PowerShell in this folder, and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\Play.cmd
```

After setup, double-click `Play.cmd` to launch the game. From a terminal, use:

```powershell
.\.venv\Scripts\python.exe -m smart_racing
```

### Controls

| Input | Action |
|---|---|
| Mouse | Navigate menus, select roads, and use on-screen race controls. |
| `Tab` / `Shift+Tab`, `Enter` | Move focus and activate a menu control. |
| `←` / `→` | Choose a road at the current junction; change the planner destination. |
| `Shift` + `←` / `→` | Change the planner's starting vertex. |
| `Enter` | Drive the selected road. |
| `N` | Use one nitro charge. |
| `F` | Refuel at an available station. |
| `Space` | Pause or resume the race; also skips the intro and broadcast overlays. |
| `Escape` | Skip the intro or return from a race screen. |

The race buttons are clickable as well. Use the view control to switch between
the projected broadcast camera and the flat tactical map. Settings retain sound
level and Reduced Motion choices between launches.

## Build, verify, and measure

Run the full suite and a headless launch check from PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests experiments scripts
.\.venv\Scripts\python.exe -m pip check
$env:SDL_VIDEODRIVER = "dummy"
$env:SDL_AUDIODRIVER = "dummy"
.\.venv\Scripts\python.exe -m smart_racing --smoke-test
```

Build the Windows executable (install the optional packager first):

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[packaging]"
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

The executable is written to `dist/SmartRacingChampionship.exe`. GitHub Actions
runs the test suite, builds and launches a packaged smoke-test copy, renders
interface previews, and builds the draft report. A headless check does not
replace a live human playthrough.

Reproduce the five algorithm studies and regenerate the report with:

```powershell
.\.venv\Scripts\python.exe experiments/benchmarks/run_studies.py
.\.venv\Scripts\python.exe -m pip install -e ".[report]"
.\.venv\Scripts\python.exe scripts/build_report.py
.\.venv\Scripts\python.exe scripts/render_report_preview.py
```

Study inputs use a fixed seed. Raw timings and analysis are saved under
`experiments/results/`. They are machine-specific measurements, not proof of
asymptotic complexity. To refresh screen previews, run
`.\.venv\Scripts\python.exe scripts/capture_previews.py`; output goes to
`output/previews/`.

Saved circuits are stored in
`%USERPROFILE%\SmartRacingChampionship\circuits`. The planner assumes a full
starting tank for its refuelling recommendation; later race events or nitro
use can change the actual outcome.

## Under the hood

- **Language:** Python 3.12+
- **Game and presentation:** Pygame
- **Circuit format:** JSON adjacency-list graphs
- **Verification:** Ruff, pytest, deterministic fixtures, integration and UI tests
- **Studies:** seeded benchmark driver with raw JSON results and analysis
- **Optional tools:** PyInstaller for Windows builds; ReportLab for PDF reports

The twelve required algorithm families are implemented manually: BFS, DFS,
Dijkstra, A*, dynamic programming, greedy selection, backtracking, Kruskal,
a binary heap / priority queue, Merge Sort, Quick Sort, and Heap Sort. The Lab
and studies reuse the game implementations. The project also includes all
three assignment extensions: seeded track generation, four weighted route
profiles, and heap-based live top-k standings.

## Project map

| Path | Purpose |
|---|---|
| `src/smart_racing/` | Algorithms, shared models, race rules, tracks, resources, events, standings, and Pygame UI. |
| `data/circuits/` | Three authored circuits. |
| `assets/` | Bundled artwork, sound, and licensed fonts with attribution. |
| `tests/` | Unit and integration test suites. |
| `experiments/` | Five study drivers, raw measurements, and analysis. |
| `docs/` | Assignment, architecture, algorithms, workflow, verification, and report. |
| `CHANGELOG.md` | Notable repository and game changes. |
| `scripts/` | Run support, previews, sound generation, report, build, and packaging tools. |
| `.github/` | Contribution/security guidance, issue/PR templates, Dependabot, and Windows CI. |
| `.editorconfig` | Shared indentation, encoding, and line-ending defaults. |

## Crew notes

- [Assignment specification](docs/assignment-specification.md) — source of
  truth for rules, algorithms, studies, bonuses, and submission requirements.
- [Assignment QA checklist](docs/testing/assignment-requirements-audit.md) —
  evidence, status, release gaps, and current estimate.
- [Development workflow](docs/development-workflow.md) — implementation,
  review, testing, and delivery procedure.
- [Visual direction](docs/architecture/visual-direction.md) — color, motion,
  camera, sound, and presentation rules.
- [Algorithm integration map](docs/algorithms/implementation-map.md) — shared
  implementations and their call sites.
- [Demo and viva guide](docs/demo-and-viva.md) — a walkthrough and explanation
  prompts for the group.
- [Technical report source](docs/report/technical-report.md) — current draft;
  group details and final review are still required.
- [Documentation index](docs/README.md) — project documents by purpose.
- [Changelog](CHANGELOG.md) — notable project changes.
- [Security policy](.github/SECURITY.md) — private vulnerability reporting.

REDLINE is the interface brand; **Smart Racing Championship** is the course
project title. Original imagery and synthesized sound are documented in
[`assets/images/README.md`](assets/images/README.md) and
[`assets/audio/README.md`](assets/audio/README.md). The bundled Barlow fonts
retain their [SIL Open Font License](assets/fonts/OFL.txt).

**Source license:** no license has been declared for the project source yet.
The font and image/audio asset notes describe their own provenance and terms;
those do not grant a license to redistribute the game code. Choose and add the
project license before accepting outside contributions or presenting the
repository as open source.
