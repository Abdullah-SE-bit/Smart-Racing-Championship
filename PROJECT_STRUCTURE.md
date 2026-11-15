# Project structure and architectural boundaries

Status: **Scaffolding Only — Not Yet Implemented**. Every Python file is an empty
package initializer. The responsibilities below describe intended future work.

The assignment specification is transcribed in
[docs/assignment-specification.md](docs/assignment-specification.md) and has been
checked against the supplied PDF. This structure remains Phase 0 scaffolding;
implementation still requires explicit user instructions.

## Source packages

| Directory under `src/smart_racing/` | Intended responsibility |
| --- | --- |
| Package root | Public package boundary; no startup behavior yet. |
| `core/` | Shared models, graph representations, configuration, and application contracts. |
| `algorithms/` | Manually implemented mandatory algorithms, independent of Pygame and presentation. |
| `algorithms/graph/` | Graph traversal and related graph operations. |
| `algorithms/routing/` | Shortest paths and route recalculation algorithms. |
| `algorithms/optimization/` | Resource allocation and other required optimization algorithms. |
| `algorithms/generation/` | Algorithms for track generation. |
| `algorithms/sorting/` | Sorting algorithms supporting rankings and required demonstrations. |
| `algorithms/structures/` | Supporting data structures used by the custom algorithms. |
| `game/` | Race lifecycle, game state, rules, timing, and domain coordination. |
| `racers/` | Human racer state, deterministic opponent strategies, and movement rules. |
| `tracks/` | Circuit loading, graph validation, checkpoints, roads, and track state. |
| `events/` | Deterministic scheduling, road closures, temporary effects, and expiration. |
| `resources/` | Fuel, nitro, pickups, refuelling, and resource constraints. |
| `championship/` | Race results, points, rankings, tie-breaking, and progression. |
| `ui/` | Pygame presentation and input translation. |
| `ui/screens/` | Main Menu, Track Explorer / Route Planner, Racing Screen, Algorithm Lab, and Championship Dashboard. |
| `ui/components/` | Reusable presentation components. |
| `ui/visualization/` | Algorithm Lab rendering of shared algorithm state or traces. |
| `utils/` | Small utilities that do not belong to a specific domain. |

## Supporting directories

| Directory | Intended responsibility |
| --- | --- |
| `assets/` | Versioned presentation assets. |
| `assets/images/` | General images. |
| `assets/sprites/` | Racer and gameplay sprites. |
| `assets/fonts/` | Fonts and associated license information. |
| `assets/sounds/` | Sound assets. |
| `data/` | Versioned JSON inputs and configuration. |
| `data/circuits/` | Definitions for the three circuits and their checkpoints and shortcuts. |
| `data/configurations/` | Game and experiment configuration inputs. |
| `data/experiments/` | JSON experiment definitions and input parameters. |
| `tests/` | Automated tests, introduced when functionality is implemented. |
| `tests/unit/` | Isolated algorithm and domain tests. |
| `tests/integration/` | Tests across domain, loading, and presentation boundaries. |
| `tests/fixtures/` | Reusable test data and fixtures. |
| `experiments/` | Reproducible experimental study tooling and artifacts. |
| `experiments/benchmarks/` | Drivers for the five required studies. |
| `experiments/datasets/` | Recorded benchmark input datasets. |
| `experiments/results/` | Raw measurements, derived summaries, and charts intended for submission. |
| `docs/` | Project documentation. |
| `docs/architecture/` | Architectural decisions and domain contracts. |
| `docs/algorithms/` | Algorithm explanations, complexity analysis, and assignment mapping. |
| `docs/testing/` | Test strategy and verification documentation. |
| `docs/report/` | Assignment report sources and submission material. |
| `scripts/` | Future maintenance and reproducibility scripts. |

Empty non-package directories contain `.gitkeep` so Git preserves them. Runtime
assets and JSON inputs remain outside the Python package for now; loading paths
and PyInstaller data inclusion must be decided before executable packaging.

## Intended relationships

The algorithm layer consumes plain Python models and contracts from `core/`.
It must not import Pygame, screens, or racing coordination. Domain modules use
these algorithms; `game/` coordinates racers, tracks, events, resources, and
championship state. The engine exposes state and accepts actions without
depending on rendering. The UI translates input into actions and renders state.
Shared models must avoid importing higher layers to prevent circular imports.

**The Algorithm Lab must reuse the exact implementations used by gameplay.**
It must not contain demonstration copies of algorithms. If stepwise observation
is needed, future algorithm contracts should expose plain Python traces or
observer data that both gameplay and the UI can consume, without rendering
inside algorithms. Experiment drivers must also call these shared algorithms.

Future deterministic behavior requires explicit random seeds where randomness
is allowed, stable tie-breaking, and an engine-controlled simulation clock for
opponents and events. Studies must record inputs, seeds, dependency versions,
measurement methods, and raw results. These are architectural intentions only;
no models, interfaces, algorithms, game behavior, or experiments exist yet.
