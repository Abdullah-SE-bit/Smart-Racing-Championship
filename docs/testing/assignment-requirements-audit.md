# Assignment requirements audit

**Audit date:** 19 November 2026
**Code reviewed:** `main` at `b93e295` (`feat(ui): tell the championship story between rounds`)
**Authority:** [complete assignment transcription](../assignment-specification.md); consult the original PDF if a transcription detail is ambiguous.

This checklist distinguishes implementation evidence from submission and human
checks. A source file or passing automated test demonstrates only the behavior
that was exercised. It does not certify a complete manual playthrough, final
submission ZIP, demonstration, viva, or course grade.

## Status key

- **PASS** — implementation is present and has direct automated or measured evidence.
- **PARTIAL** — implementation exists, but the assignment's final/manual evidence or a documented limitation remains.
- **PENDING** — depends on group information, a human action, or the later submission process.

## 1. Project scope, screens, and game rules

| Check | Status | Evidence / remaining action |
|---|---|---|
| Three distinct circuits, each with at least ten ordered checkpoints and two shortcuts | PASS | `tests/integration/test_race.py::test_three_authored_circuits_have_required_topology`; data in `data/circuits/`. |
| Intersections, alternate paths, cycles, dead ends, road conditions, fuel/nitro services and obstacles | PASS | Same topology test and circuit validator; race and route-planner integration tests. |
| Human racer plus at least three deterministic opponents | PASS | Race construction and deterministic repeat tests in `tests/integration/test_race.py`. |
| Multiple laps, ordered checkpoints, legal road movement, finish/DNF and time-limit ordering | PASS | Race integration cases include complete races, checkpoint order, closures, fuel, DNF, ties and unfinished rankings. |
| Fuel, nitro, pickups, station availability, capacity and consistent opponent rules | PASS | `test_race.py`, `test_quick_race_qa.py`, resource-planning tests; boundary values include 0, capacity limits and unavailable actions. |
| Dynamic events, required priority order, cancellation, simultaneous events, expiry and overlapping effects | PASS | Race/event integration tests cover deterministic ordering, independent expiries, persistent blocks and simultaneous events. |
| Full ten-racer points table and all championship tie-breaks | PASS | Unit and integration tests cover the ten-place points table and racer-ID final tie-break. |
| Main Menu and settings/instructions access | PASS | `tests/integration/test_ui_workflow.py`; audio and motion preference tests. |
| Track Explorer / Route Planner: reachability, alternatives, costs, comparison and ordered checkpoints | PASS | `test_route_planner_qa.py` and `test_route_planner_button_outputs.py`; authored circuits, all profiles, both route algorithms and button outputs are exercised. |
| Racing screen: cars, roads, checkpoints, race time, resources and event feedback | PASS | Race camera, HUD, event feedback and Quick Race interaction tests. |
| Algorithm Lab: step/play/pause/reset and counters using shared algorithms | PASS | `test_algorithm_lab_quality.py`, `test_lab_recordings.py`, and UI workflow Lab tests. |
| Championship Dashboard: classification, standings, statistics, sorting and top-k | PASS | Race results, all sorting choices, all-k comparisons and live standings tests. |
| Five required GUI screen functions are accessible through application flow | PASS | Headless render and navigation coverage in `test_all_screens_render_and_primary_navigation`; human usability review is still useful before submission. |
| Animation does not change simulation results; reduced-motion preference works | PASS | UI workflow, motion preference and simulation clock tests compare state and motion behavior. |

## 2. Mandatory algorithm checklist (12)

| # | Algorithm / technique | Status | Implementation and evidence |
|---:|---|---|---|
| 1 | BFS reachability and minimum-edge path | PASS | `algorithms/graph/traversal.py`; traversal tests and Study 1 reference-hop checks. |
| 2 | DFS traversal, cycles, components and bounded alternatives | PASS | `traversal.py`; mixed directed/undirected cycle and component tests; planner reports its bounded path search. |
| 3 | Dijkstra for non-negative scalar costs | PASS | `algorithms/routing/shortest.py`; independent Bellman-Ford comparisons and planner tests. |
| 4 | A* optimal routing | PASS | Shared routing implementation; tested against Dijkstra/Bellman-Ford on seeded mixed graphs and planner cases. The heuristic uses a safe lower bound, with zero fallback. |
| 5 | Dynamic programming for 0/1 Knapsack / refuelling | PASS | `algorithms/optimization/resources.py`; exhaustive small-case checks, reconstruction and refuelling-feasibility tests. |
| 6 | Greedy pickup selection | PASS | Shared resource implementation; deterministic ties, zero-cost handling and the assignment plus two further greedy-suboptimal examples. |
| 7 | Backtracking for constrained track placement | PASS | `tracks/generator.py`; seeded placement, validation rejection/retry and bounded retry tests. |
| 8 | Prim or Kruskal MST backbone | PASS | Manual Kruskal in `algorithms/generation/mst.py`; disconnected candidates rejected; generator and Lab use it. |
| 9 | Heap / priority queue for event scheduling and top-k | PASS | Manual heap in `algorithms/structures/heap.py`; event ordering/cancellation tests and live top-k tests. |
| 10 | Merge Sort for primary ranking | PASS | `algorithms/sorting/rankings.py`; common-comparator agreement tests. |
| 11 | Quick Sort for alternative ranking | PASS | Same module; random, sorted, reverse and duplicate-heavy comparisons. |
| 12 | Heap Sort for third ranking | PASS | Same module; all three sorts agree and top-k matches each full-sort prefix. |

The Algorithm Lab, gameplay, and experiments use the shared implementations;
see [implementation map](../algorithms/implementation-map.md). The Lab is not a
separate reimplementation.

## 3. Required experimental studies (5)

The studies were rerun on 19 November 2026 with
`experiments/benchmarks/run_studies.py`. The run completed its correctness
assertions and wrote raw samples to `experiments/results/studies.json` and
tables/interpretation to `experiments/results/analysis.md`. The recorded run
uses Python 3.12.16 on Windows 11, seed `20261205`, one warm-up and five timed
repetitions. Input generation, checks, rendering and file I/O are excluded from
timed regions. Results are measurements for this machine and these finite
inputs, not proof of asymptotic complexity.

| Study | Status | Coverage in the measured run |
|---|---|---|
| 1. BFS vs DFS | PASS | Sparse/dense connected graphs at 20, 60 and 120 vertices; visited/examined counts; cycle/components; independent minimum-hop verification. |
| 2. Dijkstra vs A* | PASS | Seeded graphs at 20, 60 and 120 vertices; expanded/relaxed/heap counters, runtime and equal-cost assertions. |
| 3. DP vs greedy | PASS | Assignment counterexample plus two team cases and larger item/budget inputs; selected items, benefit, states and runtime; DP checked against exhaustive subsets on the counterexamples. |
| 4. Event priority queue | PASS | 50, 250 and 1,000 events; separate insertion/extraction timing; equal keys, cancellation, heap operations and overlapping expiry verification. |
| 5. Sorting vs top-k | PASS | Random, sorted, reverse and duplicate-heavy records at 50, 200 and 500; three sorts, two k values, common-reference equality and runtime. |

## 4. Advanced challenges / bonuses (3)

| Challenge | Status | Evidence and qualification |
|---|---|---|
| Automatic track generation from MST, extra roads and constrained placement; reject and explain an invalid candidate | PASS | Seeded generator, workshop stage/retry records, real invalid-candidate demonstration and validator tests. Generated layouts belong to a documented ring-based family; this is a design limitation, not a missing challenge. |
| Multi-objective route presets (balanced, speed, economy, safety), with route changes and scalarization limits explained | PASS | All four profiles are in the planner; route comparison and closure recomputation tests; documentation gives normalized terms and a route-changing safety example. |
| Live heap-based top-k championship analytics compared with full sorting | PASS | Dashboard and shared bounded heap; all `k` values and sort agreement tested; Study 5 records small and near-`n` values. |

## 5. Assignment minimum test matrix

| Assignment test class | Status | Evidence |
|---|---|---|
| Graph: singleton, disconnected, cyclic, branching, dead-end, directed and undirected | PASS | `tests/unit/test_algorithms.py` and circuit topology tests. |
| Routing: same source/destination, unreachable, blocked, ties, zero costs and graph updates | PASS | Unit tests, all-source/target planner QA, and closure/replanning race cases. |
| Resources: insufficient fuel, full tank, unavailable service, capacity, zero-cost item, infeasible plan | PASS | Resource unit tests and Quick Race boundary/button tests. |
| Events: simultaneous order, stable ties, cancellation, expiry, missing target and overlaps | PASS | Event queue/race integration tests. |
| Sorting: empty/singleton, random, sorted, reverse, duplicate-heavy; shared comparator | PASS | Parameterized sort tests and Study 5 datasets. |
| Integration: complete race, laps, checkpoints, DNF, road closure and standings | PASS | Race and end-to-end UI workflow tests, including the three-race championship. |
| UI controls and visible outputs for planner and Quick Race | PASS | Focused button-output and Quick Race QA suites click through actual controls and inspect outcomes. |

## 6. Deliverables and release checks

| Check | Status | What remains |
|---|---|---|
| Source, circuit data, assets, run instructions and licenses/attribution | PASS | Present in repository; artwork provenance and font license are documented. |
| Application dependency health | PASS | `pip check` on audit date: “No broken requirements found.” |
| Python application smoke test | PASS | `python -m smart_racing --smoke-test` with dummy SDL video/audio exited 0. |
| Windows executable build | PASS | `scripts/build.ps1` completed successfully locally. |
| Packaged executable launch on this workstation | PARTIAL | Launch attempt is blocked by Windows Application Control before the program starts. The current [`main` GitHub Actions run](https://github.com/TahaSohail-Goat/Smart-Racing-Championship/actions/runs/44564672314) passed both `checks` and `package-smoke`, including executable and extracted test-archive launch. This is host policy, not a reported application failure. |
| Technical report structure, algorithms, correctness, tests, studies, bonuses and acknowledgements | PARTIAL | The report source has the required sections, and its 8-page PDF built and was rendered for visual inspection. It is still marked **Development draft** and group members, registration numbers and section are placeholders. Finalize those fields and review the final report. |
| Final group-specific ZIP naming, contents, extraction and malware check | PENDING | Do not submit now, per the user's instruction. CI's test-only archive is not the final group archive. Before submission, supply actual identifiers, package, inspect integrity/contents after extraction, and perform the required malware check. |
| Full human interaction rehearsal on Windows; demo and viva readiness for every member | PENDING | Automated and prior scripted playthroughs are not a substitute. Rehearse controls and demonstrate every screen, all bonuses, the three-race season and algorithm explanations on a machine that permits the executable. |

## 7. Executed on this audit

- `python -m pytest -q` — **252 passed** in 43.36 seconds.
- `python -m pip check` — **No broken requirements found**.
- `python -m smart_racing --smoke-test` with dummy SDL drivers — **exit 0**.
- `python experiments/benchmarks/run_studies.py` — **completed**; five studies, correctness assertions, five timing samples after warm-up, raw data and analysis regenerated.
- `scripts/build_report.py` — **completed**; report PDF generated.
- `scripts/render_report_preview.py` — **completed**; 8 pages rendered. The montage was visually inspected; no obvious clipping or page-layout failure was seen at the montage scale.
- `scripts/build.ps1` — **completed**; Windows executable built.
- Local executable launch — **blocked before startup** by Windows Application Control. GitHub Actions run for commit `b93e295` completed successfully, including `checks` and `package-smoke`.

## 8. Score estimate (not an instructor grade)

The assignment provides requirements, not a numeric grading rubric. This
evidence-based planning estimate weights the criteria as follows:

| Area | Weight | Current estimate | Reason |
|---|---:|---:|---|
| Required game scope and mechanics | 30 | 28 | Coverage and integration tests are broad; a human playthrough remains. |
| Mandatory algorithms and gameplay/Lab integration | 25 | 24 | All 12 are present, shared and tested; final demonstration must explain them. |
| Testing and experimental evidence | 20 | 19 | Full suite and five studies pass; study samples are finite and single-machine. |
| Three bonus challenges | 15 | 14 | All are implemented and evidenced; generated layouts are ring-based. |
| Report and submission readiness | 10 | 5 | Report builds but needs group details/final review; final named ZIP, allowed-machine executable check, human demo and viva are pending. |
| **Total current evidence estimate** | **100** | **90** | Strong implementation evidence; not yet fully submission-ready. |

The **90/100 is a project-readiness estimate only**, not a promise of marks.
An instructor may weight the report, manual demonstration, originality,
requirements interpretation or viva differently. It would be inaccurate to
claim 100% completion while the explicitly listed human and submission checks
are open.

## Before submission: close these remaining items

- [ ] Enter the actual member names, registration numbers and section in the report.
- [ ] Review the final PDF page by page and confirm the references, assets and results are accurate.
- [ ] On an allowed Windows machine, launch the built executable and complete a human Quick Race and full championship; inspect all five screens and each bonus.
- [ ] Rehearse the demonstration and confirm every group member can explain the implementation and experiments.
- [ ] Build the final ZIP with the required registration-number/section name; inspect ZIP integrity, required contents and extracted execution; perform the assignment's malware check.
- [ ] Re-run the test suite and dependency check against the exact final source/archive, recording the results.
