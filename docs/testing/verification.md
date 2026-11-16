# Verification in progress

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

The latest recorded local run used Python 3.12.16 on Windows and reported
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
