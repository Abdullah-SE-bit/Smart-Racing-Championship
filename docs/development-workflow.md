# Development workflow and delivery map

This guide maps the complete assignment to practical work. The
[assignment specification](assignment-specification.md) is the source for exact
rules, formulas, examples and deliverables; consult the original PDF if wording
is unclear. The playable implementation and assignment bonuses are in place;
consult the [assignment-wide QA audit](testing/assignment-requirements-audit.md)
for verified behavior and the release work that remains. This map is a guide,
not a set of approval gates.

## Working together

1. Read [AGENTS.md](../AGENTS.md), [README.md](../README.md),
   [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md), and the assignment sections
   relevant to the change. Inspect existing work and related issues.
2. Choose or create a reasonably sized issue. Use relevant type, area, scope,
   and priority labels; coordinate ownership with the team. The original broad
   issues #191–#198 are overview trackers, and the more focused issues describe
   implementable pieces. Split, combine, reorder or add work as needed.
3. Agree on contracts when tasks meet: graph data, route results, engine actions,
   event ordering, algorithm traces and screen inputs. Record consequential
   decisions and tuned rules in `docs/architecture/`.
4. Work on a short-lived branch from `main`, connect related changes to their
   issue, and open a pull request. The protected `main` branch requires the
   `checks` and `package-smoke` CI jobs to pass before merging; no approval is
   required. Agent commits and pushes require explicit permission.
5. Include meaningful tests with implemented behavior, update documentation, and
   share screenshots or a recording for visual changes. Explain what was actually
   checked. Review and merge, then clean up temporary branches where appropriate.

Labels and issue relationships are for visibility, not enforced prerequisites.
Teams may work in parallel and adapt this order as they learn. Keep the assignment
and all bonuses covered when issue scope changes.

## Suggested path through the work

### 1. Establish shared foundations

- Specify graph, racer, event, result and championship records; use adjacency
  lists and stable IDs, with directed/undirected edges, road status, non-negative
  costs, difficulty and service state. Document configuration and serialization.
- Establish a simulation clock, seeded inputs, stable tie-breaking, a recovery
  policy and clear interfaces between domain logic and Pygame. Record tunable
  fuel, nitro, lap, event, scoring and time-limit settings before experiments.
- Create and validate three distinct authored circuits, each meeting the
  assignment's checkpoint, shortcut, topology, service and obstacle requirements.
  Verify ordered checkpoint and lap return reachability, alternative routes, and
  a feasible fuel plan including directed edges.

### 2. Implement and integrate algorithms

Implement the mandatory algorithms manually in `src/smart_racing/algorithms/`.
Gameplay, Lab, and experiments call these same implementations. Expose reusable
plain-data traces and counters where needed, without importing Pygame.

| Work | Functional role and checks |
| --- | --- |
| BFS and DFS | Reachability, minimum-edge path, traversal, components, cycles, dead ends and bounded alternative paths; handle disconnected graphs. |
| Dijkstra and A* | Optimal non-negative scalar cost routes, ordered checkpoint legs and replanning; document normalization and admissible heuristic, using a safe fallback where needed. |
| Dynamic programming and greedy | 0/1 pickup selection and refuelling planning; reconstruct feasible choices, handle zero-cost items and deterministic ties; compare with exhaustive small cases. |
| Heap and event queue | Deterministic priority operations and top-k support; events order by time, priority and insertion sequence; cancellation uses lazy deletion. |
| MST and backtracking | Connected undirected backbone and constraint-based placement; document pruning and validate resulting directed playability. |
| Merge, Quick and Heap Sort | Complete championship rankings with one comparator, consistent with heap top-k. |

Document input/output contracts, correctness assumptions, complexity and actual
gameplay call sites under `docs/algorithms/`. Follow the assignment for detailed
cases, including its greedy counterexample and two additional team-created cases.

### 3. Build the race and championship

Connect legal edge movement, checkpoint order, lap completion, clock and time
limits, finish/DNF handling and race results. Apply fuel and nitro mechanics to
players and opponents alike. Implement the three documented opponent strategies
and their refuelling behavior. Process simultaneous events before replanning;
validate targets, cancel lazily, expire overlapping effects independently and
apply a documented recovery policy if no route is available. Implement the full
points table and championship comparator including every tie-breaker.

### 4. Build the animated interface

Create coherent navigation, styling, useful motion, responsive feedback and
attributed assets across all five screens:

1. **Main Menu:** Championship, Quick Race, Algorithm Lab, instructions and settings.
2. **Track Explorer / Route Planner:** graph, reachability, alternate routes,
   route costs, comparison and resource recommendations.
3. **Racing Screen:** moving cars and roads, ordered checkpoints, clock, fuel,
   nitro, events and route feedback.
4. **Algorithm Lab:** step/play/pause/reset visualizations and counters driven by
   the actual algorithms and project data.
5. **Championship Dashboard:** race results, standings, statistics and top-k.

Make state readable and controls discoverable. Rendering and animation must not
change engine outcomes; check usability and the complete navigation flow.

### 5. Complete all advanced challenges

- Generate seeded, playable circuits from a connected candidate graph, an MST,
  extra roads and backtracking placement; show a rejected invalid candidate with
  its reason, and validate directed checkpoint and fuel feasibility.
- Compare balanced, speed, economy and safety presets using documented normalized
  non-negative weights. Show component costs and a case where choices differ;
  explain the limitations of combining objectives into one scalar.
- Show live heap-based top-k standings, compare them with full sorting for
  different `n` and `k`, and use the same total comparator everywhere.

### 6. Test, measure, report and deliver

- Add unit and integration tests alongside implementation: graph edge cases,
  routing optimality, legal movement, resource feasibility, deterministic events
  and opponents, scoring ties, sorting agreement and end-to-end races. Verify
  the Lab and experiments use the gameplay implementations.
- Run Ruff (`python -m ruff check src tests experiments scripts`), pytest,
  and `pip check`. CI runs these checks on every pull request and push to `main`;
  a missing test suite is a failure, not a skipped check.
- Run all five studies: BFS vs DFS, Dijkstra vs A*, DP vs greedy, event priority
  queue, and sorting vs top-k. Use repeatable inputs and seeds, multiple sizes,
  warm-up and repeated measurements; exclude rendering and I/O from timed regions.
  Save methods, environment, raw measurements, tables, charts and interpretation.
  Never fabricate results. See assignment section 7 for each required metric.
- Write the report with architecture, rules, pseudocode, correctness, complexity,
  integration, tests, experiments, limitations, bonuses and acknowledgements.
  Keep asset licenses and versioned submission materials with the project.
- Prepare a functional executable, source, assets, setup/run instructions,
  report and experimental results. Check the required ZIP name and contents,
  verify extraction and execution, and prepare every group member for the demo
  and viva. Follow the assignment for the final submission procedure and deadline.

Update the README with actual run and packaging commands once those exist. Do not
present unimplemented work, empty test collections or hypothetical results as done.
