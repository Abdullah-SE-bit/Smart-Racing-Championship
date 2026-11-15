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
**83 passed**. Rerun the suite after further changes; the count and outcome may
change. `pip check` reported no broken requirements. A separate check generated
and validated 100 seeds; five seeded tracks were also raced in automated tests.
Saved circuits with nonconsecutive IDs are exercised through selection,
planning, and scheduled race events.
The planner's alternative-route view and its state, route-count, and path-length
limits are also covered by unit and headless interface tests.
Championship navigation visits the planner before each race and preserves the
fixed circuit order and accumulated standings in the three-race workflow.

The headless screen smoke tests do not replace a human playthrough. Before final
submission, perform a complete manual quick race and championship on a Windows
machine, try the Lab and planner controls, verify the generated circuit and
bonus views, run the built executable, and check the extracted submission ZIP.
Record actual outcomes and failures instead of assuming a successful build means
the game can run.
