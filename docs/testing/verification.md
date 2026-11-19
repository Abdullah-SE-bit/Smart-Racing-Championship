# Verification in progress

## Assignment-wide verification snapshot (19 November 2026)

See the [assignment requirements audit](assignment-requirements-audit.md) for
the requirement-by-requirement checklist, test evidence, pending human/release
items and a clearly qualified readiness estimate. On this date the full local
suite passed **252 tests** in 43.36 seconds; `pip check`, the Python smoke test,
all five measured studies, report generation/rendering, and the Windows
executable build completed. Local launch of that executable was blocked by
Windows Application Control before startup. GitHub Actions for `main` commit
`b93e295` passed both `checks` and `package-smoke`. The report remains a draft,
and a final group-specific ZIP, human playthrough, demonstration and viva are
still pending.

## Algorithm Lab quality coverage

`tests/integration/test_algorithm_lab_quality.py` applies boundary-value
analysis to backward, zero, forward, exact-end, over-end and corrupted
playback indices. It renders every selectable algorithm at the beginning,
near the midpoint and at the end of its trace on both an authored and a
seeded generated circuit. It also checks that repeated rendering leaves the
trace deterministic and does not advance a live race, that circuit and
championship changes invalidate cached trace data, and that playback stops at
the final record and can replay. Each case runs with the dummy SDL video and
audio drivers for reproducibility.

Run the automated suite from the repository root with Python 3.12:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pip check
```

The current suite exercises graph traversal and routing, heuristic agreement,
heap behavior, dynamic programming versus exhaustive search, greedy
counterexamples, sorting and top-k, circuit loading and generation, event
ordering and overlapping expiry, resources, repeatable races on all three
authored circuits, championship points, and headless screen rendering.

An earlier local run used Python 3.12.16 on Windows and reported
**90 passed**. Rerun the suite after further changes; the count and outcome may
change. `pip check` reported no broken requirements. A separate check generated
and validated 100 seeds; five seeded tracks were also raced in automated tests.
The resource-planning changes were subsequently checked locally with Python
3.12.16: **111 passed**, including ordered pickup recommendations, nitro
capacity and the reconstructed refuelling screen. This run used the existing
virtual environment's packages with an allowed base Python executable.
The clickable race-control change was subsequently checked with **112 passing
tests**. In a visible Windows game window, clicking Drive reached checkpoint 1,
Next Road selected checkpoint 2, and Pause changed to Resume. Automated
keyboard injection did not produce visible actions during this inspection;
physical keyboard operation has not been established by that observation.
The subsequent shortcut-routing change passed **114 tests** locally, including
a shortcut with a multi-road approach and exit, closure during an approach,
and rejection of a route through a later checkpoint.
The road-identity change passed **116 tests** locally, including parallel
directed and undirected roads, a selected road closing before entry, and an
opponent taking a designated shortcut that shares its endpoints.
After adding one-way generated roads, **116 tests** passed locally. A separate
check generated and validated seeds 0 through 99 and confirmed that each track
contains two roads traversable only in their declared direction. These sampled
seeds do not establish success for every possible seed.
The blocked-road feedback update passed **117 tests** locally, including a
selected parallel road closing before entry and visible warnings for an
unavailable route and insufficient fuel.
The mixed-graph cycle fix passed **119 tests** locally. Its regression cases
include parallel one-way and two-way roads, blocked roads and 300 seeded small
graphs compared with an independent exhaustive cycle search.
The weak-component traversal update passed **120 tests** locally, including
2,000 vertices with directed, parallel and blocked roads and many isolates.
An independent Bellman-Ford comparison subsequently passed on 160 seeded
four-vertex mixed graphs for every source and destination, checking 5,120
Dijkstra and A-star results and their road IDs. The full suite reported
**121 passed** locally. These samples are not a proof for all graphs.
The road-effect precedence fix subsequently passed **124 tests** locally,
including independent permanent road blocks and shortcut states, plus
temporary closures overlapping oil, restriction and shortcut-open effects.
The indexed routing heap update passed **126 tests** locally, including seeded
heap operations, 100 parallel roads with repeated key decreases, and the
independent Bellman-Ford routing comparison. All five recorded studies were
rerun on the documented local environment after the routing change.
The Lab verification update passed **128 tests** locally. All selectable Lab
modes were rendered and stepped on an authored circuit and a mixed-direction
generated circuit, including the no-feasible-pickup case where applicable.
Reset was also checked after a step count greater than 10,000.
The latest recorded GitHub Actions run for PR #247 passed **94 tests** on Windows
with Python 3.12 and found no broken requirements. Later changes require a new run.
The run for PR #254 subsequently passed **105 tests** on Windows with Python
3.12. The local Python executable was blocked by Windows Application Control;
later runs must be checked separately.
The Windows run for PR #257 passed **108 tests**, `pip check`, preview rendering,
and a separately built executable's headless smoke test. All ten generated
screen previews from the prior preview workflow were visually inspected. The
local executable remains blocked by Application Control. The package-smoke job
also checks the executable after extraction from a temporary executable-only
test archive. That archive is not the final submission package and does not
verify group-specific naming or the complete submission contents.
The local submission packager was also exercised with explicitly test-only
identifiers: the ZIP passed its integrity check, required files were present
after extraction, and the extracted executable and report matched their source
hashes. The host blocked the local built executable, so this did not verify
its launch. The CI package-smoke workflow is configured to perform the full
test-archive check and launch from the extracted directory on its Windows
runner, using a report rebuilt from the current source. Neither test archive is
the final group-specific submission.
The full test-archive workflow passed in Windows CI for PR #284, including
launch of the extracted executable from its own directory.
Saved circuits with nonconsecutive IDs are exercised through selection,
planning, and scheduled race events.
The planner's alternative-route view and its state, route-count, and path-length
limits are also covered by unit and headless interface tests.
The route-comparison animation is checked against actual route vertices and the
reduced-motion setting.
Championship navigation visits the planner before each race and preserves the
fixed circuit order and accumulated standings in the three-race workflow.
Opponent tests cover low-fuel and fixed detours near future checkpoints,
including main routes with service vertices between checkpoints.
Generation-stage tests cover the workshop, a real rejected attempt and retry,
and the separate invalid-track validation demonstration.
The experiment harness independently verifies minimum hop counts before timing;
its reference is tested with directed, blocked and unreachable roads.
The greedy trace keeps running benefit and cost totals for 3,000 pickups, and
its final selection is checked against the untraced implementation. The local
suite passed 129 tests after this change; all measured studies were rerun.

## Route planner focused QA (19 November 2026)

The route planner received boundary-value, equivalence-class, state-transition,
integration and visual checks. `tests/integration/test_route_planner_qa.py`
compares Dijkstra and A* for every source/target pair on all three authored
circuits, under all four cost profiles. For every reachable result it validates
the endpoints, edge count, legal directed traversal and recomputed path cost;
unreachable results must return no path and infinite cost. Additional cases
exercise minimum/maximum vertex navigation, wraparound, a zero-length route,
ordered checkpoint laps, switching the routing algorithm through its UI
control, a fully disconnected graph, and planner action hitboxes within the
expanded panel. `tests/integration/test_route_planner_button_outputs.py`
clicks every planner button and verifies its resulting state or output: all
four profiles, ordered/direct mode, comparison rows and return, algorithm
switching, refuelling and alternatives navigation, generated-circuit validation,
season-order protection, quick/championship race startup, save and invalid-track
feedback. Refuelling pagination is exercised with a real route requiring more
than six stops. The profile-chip UI test uses the updated chip location.

On Python 3.12.16 / Windows, the focused planner checks passed **20 tests** and
the complete suite passed **230 tests**. `pip check` reported no broken
requirements; `python -m smart_racing --smoke-test` exited successfully.
`scripts/capture_previews.py` rendered all screens, and the
1280×800 planner preview was visually inspected for clipping, overlap and
control alignment. The preview is a headless render, not a substitute for a
manual mouse-and-keyboard playthrough.

## Quick Race focused QA (19 November 2026)

`tests/integration/test_quick_race_qa.py` drives the actual mouse controls for
camera mode, previous/next road, drive, boost, refuel, pause/resume, main-menu
return and results. Boundary-value cases cover fuel at 0, 60, 99 and 100 units,
nitro at 0, 1 and 3 charges, repeated refuelling at one station, refuelling away
from a station, and road-choice wraparound at a junction. It checks Quick Race
entry on each authored circuit, four starting racers and a full player tank.
Existing race tests cover checkpoint order, lap completion, blocked and
restricted roads, event ordering, deterministic opponents, DNF and results.
`tests/integration/test_quick_grid.py` checks menu/planner entry, countdown
simulation freeze and release, skip input isolation, reduced motion and the
championship path.

The Quick Race focused set passed **63 tests** and the full suite passed **249
tests** on Python 3.12.16 / Windows. `pip check`, the headless application smoke
test and `git diff --check` passed. The updated 1280×800 start grid and live race
with nitro were rendered and visually inspected. The earlier full run caught
one outdated interaction test that attempted boost before skipping the new grid
countdown. The test now explicitly starts the race before asserting boost.

The headless screen smoke tests do not replace a human playthrough. Before final
submission, perform a complete manual quick race and championship on a Windows
machine, try the Lab and planner controls, verify the generated circuit and
bonus views, run the built executable, and check the extracted submission ZIP.
Record actual outcomes and failures instead of assuming a successful build means
the game can run.

`scripts/capture_previews.py` renders the screen flow to `output/previews/` with
the dummy SDL driver. CI uploads those images as an artifact for visual review;
the previews are generated from the app and a simulated race, not a recording of
a human playthrough.

## REDLINE presentation and assignment verification

The local Python 3.12.16 suite passed 146 tests and pip check reported no broken requirements. Screen previews covered both race cameras, the race results, standings and the Lab's graph, heap, sorting and budget views.

A separate scripted playthrough sent mouse and keyboard events through the application and advanced its fixed-step clock. It selected Championship from the menu, drove the three authored two-lap races, switched camera, and opened results and standings after each round. All four racers finished each round. The championship awarded 70, 140 and 210 cumulative points and returned to the menu after the finale. The player's finishing times were 24.10, 24.07 and 24.07 simulation seconds. A human rehearsal and the group's submission details remain outstanding.
