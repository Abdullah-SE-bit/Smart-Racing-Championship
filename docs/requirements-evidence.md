# Assignment requirements and evidence

This map connects the assignment transcription to the source and recorded
verification. An implementation or automated test is evidence only for the
cases exercised. For the current full checklist, latest test run, and release
gaps, see the [assignment-wide QA audit](testing/assignment-requirements-audit.md)
and [verification history](testing/verification.md). The assignment and
original PDF remain authoritative.

## Game, screens and rules

| Assignment area | Implementation and evidence | Remaining review |
| --- | --- | --- |
| Three distinct circuits, ten checkpoints, shortcuts, intersections, cycle, dead end and services | `data/circuits/`; `tracks/circuits.py`; `test_three_authored_circuits_have_required_topology` | Play each authored circuit through the packaged game. |
| Main menu, quick race, championship and settings | `ui/app.py`; `test_all_screens_render_and_primary_navigation` | Complete an interactive playthrough. |
| Explorer, route comparison, alternatives and ordered checkpoint planning | `ui/app.py`; `test_planner_alternatives_show_real_bounded_paths`; `test_route_presets_recompute_exact_costs_after_a_road_closes` | Check the controls and route explanations in a human review. |
| Racing HUD, movement, resources and event feedback | `game/race.py`, `ui/app.py`; `test_race_controls_support_mouse_actions`; race integration tests | Complete a human race including refuelling, nitro and an active closure. |
| Algorithm Lab using shared implementations | `ui/app.py`, `algorithms/`; `test_algorithm_lab_uses_current_track_and_championship_data` | Review all algorithm traces interactively. |
| Results, standings and top-k | `championship/standings.py`; `test_live_championship_leaders_follow_changed_results_and_every_k` | Review the standings during a complete human championship. |
| Legal roads, ordered checkpoints, multiple laps and recovery | `game/race.py`; `test_out_of_order_checkpoint_and_early_start_crossing_do_not_count`; `test_no_route_waits_until_a_closure_expires` | Exercise recovery and multiple laps in a human playthrough. |
| Fuel, nitro, pickups and refuelling rules | `game/race.py`, `resources/planner.py`; resource and race tests | Check recommendations against a full interactive race. |
| Three deterministic opponent strategies | `game/race.py`; `test_seed_and_events_reproduce_opponent_decisions_each_tick`; shortcut and fuel-detour tests | Observe all strategies and recovery in full races. |
| Events, priority, cancellation and overlapping expiry | `events/queue.py`, `game/race.py`; `test_event_order_cancellation_and_independent_expiration`; `test_expired_and_overlapping_road_effects_restore_correctly` | Review representative event scenarios in the running game. |
| Points for up to ten racers and championship tie-breaks | `championship/standings.py`; `test_full_ten_racer_points_table`; `test_championship_sorts_and_top_k_use_all_tie_breakers` | Confirm the final demonstration explains the ranking. |

## Algorithms

The [implementation map](algorithms/implementation-map.md) identifies the
shared functions and their actual game, Lab and experiment call sites.

| Required family | Main source | Example evidence |
| --- | --- | --- |
| BFS and DFS | `algorithms/graph/traversal.py` | Traversal, bounded-path, mixed-cycle and weak-component unit tests. |
| Dijkstra and A-star | `algorithms/routing/shortest.py` | Routing tests include closures, equal costs and zero weights; both algorithms are compared against an independent Bellman-Ford reference on seeded mixed graphs. |
| Dynamic programming and greedy | `algorithms/optimization/resources.py`, `resources/planner.py` | Knapsack and refuelling tests compare against exhaustive small cases; greedy counterexamples are checked. |
| Backtracking and Kruskal | `tracks/generator.py`, `algorithms/generation/mst.py` | Seeded generation, rejection, connectivity and mixed-direction Lab tests. |
| Heap and event priority queue | `algorithms/structures/heap.py`, `events/queue.py` | Heap ordering, cancellation, simultaneous events and expiry tests. |
| Merge Sort, Quick Sort and Heap Sort | `algorithms/sorting/rankings.py` | Sort and top-k agreement and championship tie-break tests. |

## Studies and advanced challenges

| Requirement | Implementation and evidence | Remaining review |
| --- | --- | --- |
| Five experimental studies | `experiments/benchmarks/run_studies.py`; measured tables in `experiments/results/analysis.md`; raw samples in `studies.json` | Confirm recorded results and interpreter environment match the final release. |
| Generated circuits | `tracks/generator.py`; seeded generation and five generated-race tests; 100 seeds checked locally | Review generator constraints and demonstrate a rejected candidate. |
| Multi-objective routing | Four `CostProfile` presets in `ui/app.py`; route comparison tests and the report's normalized formula | Demonstrate a case with different selected routes and explain scalarization limits. |
| Live top-k standings | `championship/standings.py` and the standings screen; all-k agreement tests and study 5 | Demonstrate updates after actual race results. |

## Delivery and human work

- The current report source and generated PDF are drafts. Group member names,
  registration numbers and section are not available in this workspace.
- The test suite and Windows CI exercise the game and a headless executable
  smoke check. The packaged executable was blocked on this computer by its
  application-control policy. A source launch was observed using an allowed
  Python runtime; a full human playthrough remains outstanding.
- `scripts/package_submission.py` can create and inspect a local ZIP after
  actual group details and final artifacts are available. The final ZIP's name,
  contents, extraction, offline execution and malware check remain unverified.
  CI is configured to exercise the same packager with test-only identifiers and
  smoke-test its extracted executable; that test is not a final submission.
- The group must rehearse the demonstration and viva and verify that every
  member understands the project. See [the demo guide](demo-and-viva.md).
- The user has instructed us not to submit now. Creating or uploading a final
  submission is not part of the current work.
