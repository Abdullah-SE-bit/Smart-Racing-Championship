# Project structure and architectural boundaries

Status: **Implementation in progress**. The responsibilities below describe
the current code and reserved package boundaries. See the
[requirements evidence map](docs/requirements-evidence.md) for implemented
features and work that still needs verification.

The assignment specification is transcribed in
[docs/assignment-specification.md](docs/assignment-specification.md) and has been
checked against the supplied PDF. The user has authorized implementation.

## Source packages

| Directory under `src/smart_racing/` | Intended responsibility |
| --- | --- |
| Package root | Public package boundary and `python -m smart_racing` entry point. |
| `core/` | Shared models, graph representations, configuration, and application contracts. |
| `algorithms/` | Manually implemented mandatory algorithms, independent of Pygame and presentation. |
| `algorithms/graph/` | Graph traversal and related graph operations. |
| `algorithms/routing/` | Shortest paths and route recalculation algorithms. |
| `algorithms/optimization/` | Resource allocation and other required optimization algorithms. |
| `algorithms/generation/` | Algorithms for track generation. |
| `algorithms/sorting/` | Sorting algorithms supporting rankings and required demonstrations. |
| `algorithms/structures/` | Supporting data structures used by the custom algorithms. |
| `game/` | Race lifecycle, game state, rules, timing, and domain coordination. |
| `racers/` | Reserved package; racer state and opponent strategies currently live in `game/race.py`. |
| `tracks/` | Circuit loading, graph validation, checkpoints, roads, and track state. |
| `events/` | Deterministic scheduling, road closures, temporary effects, and expiration. |
| `resources/` | Pickup and refuelling recommendations; the race engine applies resource rules. |
| `championship/` | Race results, points, rankings, tie-breaking, and progression. |
| `ui/` | Pygame presentation and input translation. |
| `ui/app.py` | Main Menu, planner, race, Algorithm Lab, dashboard and shared presentation helpers. |
| `ui/screens/`, `ui/components/`, `ui/visualization/` | Finish classification, broadcast components, circuit scenery, race cameras and algorithm trace graphics. |
| `utils/` | Reserved package for utilities that do not belong to a specific domain. |

## Supporting directories

| Directory | Intended responsibility |
| --- | --- |
| `assets/` | Versioned presentation assets included in the Windows build. |
| `assets/images/` | Original generated pit-lane artwork and its provenance. |
| `assets/sprites/`, `assets/fonts/`, `assets/sounds/` | Bundled Barlow typefaces and OFL license in fonts. Sprite and sound directories are reserved. |
| `data/` | Versioned JSON inputs and configuration. |
| `data/circuits/` | Definitions for the three circuits and their checkpoints and shortcuts. |
| `data/configurations/`, `data/experiments/` | Reserved input directories; current settings and study inputs are defined in code. |
| `tests/` | Automated unit and integration tests. |
| `tests/unit/` | Isolated algorithm and domain tests. |
| `tests/integration/` | Tests across domain, loading, and presentation boundaries. |
| `tests/fixtures/` | Reserved for reusable fixture files; current fixtures are created in tests. |
| `experiments/` | Reproducible experimental study tooling and artifacts. |
| `experiments/benchmarks/` | Driver for the five required studies. |
| `experiments/datasets/` | Reserved dataset directory; the study driver generates seeded inputs. |
| `experiments/results/` | Raw measurements, derived summaries, and charts intended for submission. |
| `docs/` | Project documentation. |
| `docs/architecture/` | Architectural decisions and domain contracts. |
| `docs/algorithms/` | Algorithm explanations, complexity analysis, and assignment mapping. |
| `docs/testing/` | Test strategy and verification documentation. |
| `docs/report/` | Assignment report sources and submission material. |
| `scripts/` | Build, preview, report and local submission-packaging scripts. |

Empty non-package directories contain `.gitkeep` so Git preserves them. Circuit
JSON lives outside the Python package in source checkouts. The PyInstaller build
includes `data/circuits` and the app resolves that bundled data at runtime;
Windows CI builds and smoke-tests the executable. The final submission package
still requires separate verification.

## Relationships

The algorithm layer consumes plain Python models and contracts from `core/`.
It must not import Pygame, screens, or racing coordination. Domain modules use
these algorithms; `game/` coordinates racers, tracks, events, resources, and
championship state. The engine exposes state and accepts actions without
depending on rendering. The UI translates input into actions and renders state.
Shared models must avoid importing higher layers to prevent circular imports.

**The Algorithm Lab must reuse the exact implementations used by gameplay.**
It must not contain demonstration copies of algorithms. Shared algorithms expose
plain Python traces for stepwise observation without rendering inside algorithms.
Experiment drivers also call these shared algorithms.

Deterministic behavior requires explicit random seeds where randomness
is allowed, stable tie-breaking, and an engine-controlled simulation clock for
opponents and events. Studies must record inputs, seeds, dependency versions,
measurement methods, and raw results. Continue checking these requirements as
the game and studies are implemented.
