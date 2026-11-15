# Testing strategy and requirement mapping

The assignment PDF is absent, so this mapping covers supplied requirements only.
Application functionality is not implemented. CI infrastructure checks do not
prove the following future behavior.

| Requirement / layer | Required evidence when implemented |
| --- | --- |
| Unit and regression | Small domain tests, explicit invalid inputs, and a regression test for each reproducible defect. |
| BFS | Minimum-edge paths, unreachable nodes, start equals goal, and deterministic ties. |
| DFS | Traversal, cycle handling, connected components, disconnected inputs. |
| Dijkstra | Optimal cost on independently checkable graphs, unreachable nodes, rejected unsupported weights. |
| A* | Optimal cost agrees with a reference expectation; admissibility/consistency assumptions and termination conditions documented and tested. |
| DP | Optimality on small exhaustive inputs, reconstruction, feasibility and boundary capacities. |
| Greedy | Selection policy, documented limits, deterministic ties, counterexamples where appropriate. |
| Backtracking / MST | Constraints and valid rejection; spanning coverage, no cycles, correct total weight and disconnected policy. |
| Heap | Ordering, empty/singleton behavior and stable same-tick event ties. |
| Merge / Quick / Heap Sort | Sortedness, permutation preservation, duplicates and ties, empty and adversarial inputs; stability only where required. |
| Top-k | Equivalence with full sorting for agreed tie and boundary policies. |
| Circuits | Exactly three valid circuits; each has at least ten mandatory checkpoints and two shortcuts, graph reachability and JSON validation. |
| Race integration | Ordered checkpoints, fuel/nitro bounds, closures and route recalculation, finish and DNF behavior. |
| Determinism | One human plus three deterministic opponents; repeated inputs/seeds/ticks yield identical decisions, events and results. |
| Championship | Assignment points, ranking, tie-breaking, and progression with independent expected examples. |
| Five GUI screens / Lab | Input-state transitions, Lab calls exact gameplay algorithms, and manual screen/play evidence. |
| Five studies | Drivers execute on small CI inputs, correctness checked, required output files/schema verified, raw measurements and metadata recorded. |
| Windows packaging | Real entry point, PyInstaller build on Windows, expected executable/data/assets, and launch/manual verification outside source checkout. |

Use pytest discovery under `tests/`; place isolated checks in `tests/unit/`,
cross-module checks in `tests/integration/`, and reusable inputs in
`tests/fixtures/`. Optional registered markers describe algorithm, regression,
determinism, integration, experiment, and packaging checks. CI runs the full
suite; no marker filter silently excludes new tests.

Check invariants such as path continuity/cost, sorting permutation, resource
bounds and event ordering with small exhaustive inputs or deterministic input
generation. No property-testing dependency is necessary initially.

Linux and Windows run pytest with dummy SDL video/audio drivers. Headless tests
cannot replace manual visual review, controls, audio, gameplay feel, or real
Windows executable checks. Record manual OS/version/input/expected/actual
evidence in PRs and handoffs.

When adding a capability, update specific `test_paths` and mark its manifest
entry implemented in the same PR. Split broad entries for partial capabilities;
do not wait for all twelve algorithms before activating a completed algorithm's
gate. The runner rejects missing, uncollected, or entirely skipped matching test
files. Reviewers still assess coverage: a passing test file cannot prove every
requirement. Infrastructure tests count only as infrastructure evidence.

For studies, record seeds, datasets, environment/dependency versions, commands,
raw format, correctness, and derived plots. Do not enforce fixed timings or
compare speed thresholds across GitHub runners. Activate build and experimental
tests when actual entry points/drivers are implemented; do not create fake ones.
