# Smart Racing Championship - Technical Report

## Project information and status

Course: Design and Analysis of Algorithms. The group registration numbers and
section have not been supplied in this workspace and must be added before the
submission ZIP is named. This is a report on the current implementation, not a
claim that the submission is complete.

## Problem and objectives

The project models a racing circuit as a graph. A player and three deterministic
opponents travel through ordered checkpoints, manage fuel and nitro, and react
to changes in road availability. The implementation aims to connect each
required algorithm to a racing, planning, visualization, or championship task.
The assignment's precise requirements and constraints are retained in
`docs/assignment-specification.md`.

## Architecture and game flow

The shared graph and race engine contain no Pygame rendering. Pygame presents
the main menu, settings, route explorer, racing screen, Algorithm Lab, results,
and standings. The Lab consumes the same algorithm functions as the planner,
race and experiments. Authored JSON circuits and seeded generated circuits are
loaded as adjacency-list graphs. A fixed 1/30-second simulation step separates
the race clock from animation frame rate. See `docs/architecture/decisions.md`
for tuned rules and recovery choices.

## Models and rules

Vertices identify the start, checkpoints, intersections and services. Edges
identify directed or undirected roads with distance, time, fuel, difficulty,
status, shortcut and obstacle attributes. The route cost is a weighted sum of
normalized distance, time, difficulty-adjusted fuel, difficulty and obstacle
terms. All weights are non-negative. Four route presets use different weights;
their scalar scores use different scales and should not be compared directly.

The current defaults are two laps, a 240-second limit, a 100-unit fuel tank,
up to 40 units per station visit, a three-second stop and an initial nitro
charge. Nitro lasts four simulation seconds, increases speed by 1.5 and doubles
fuel use for the affected portion. The score table and total championship
tie-break order follow the assignment. Unfinished racers receive no points.

## Algorithm design and integration

| Algorithm | Current role | Time / space |
| --- | --- | --- |
| BFS | Reachability and minimum-edge paths in exploration | O(V+E) / O(V) auxiliary |
| DFS | Traversal, with cycle, weak-component, dead-end and bounded path helpers | O(V+E) traversal / O(V); path enumeration can be exponential |
| Dijkstra | Non-negative route optimization and opponent routing | O((V+E) log V) with a binary heap |
| A* | Heuristic route search and comparison | Worst case comparable to Dijkstra; depends on heuristic |
| Dynamic programming | 0/1 pickup choices and discrete fixed-route refuelling | O(mB) for knapsack with reconstruction; direct refuelling O(mC²) |
| Greedy | Feasible benefit-to-cost pickup comparison | O(m log m) sorting |
| Backtracking | Ordered checkpoint placement during generation | Exponential worst case |
| Kruskal | Undirected generated-circuit backbone | O(E log E) with union-find |
| Binary heap | Route queue, deterministic event queue and top-k | O(log n) insert/extract; O(1) peek |
| Merge Sort | Primary championship ranking | O(n log n) time, O(n) space |
| Quick Sort | Alternate standings comparison | O(n log n) average, O(n²) worst case |
| Heap Sort | Alternate standings comparison | O(n log n) time, O(1) auxiliary space after copying |

The A* heuristic uses straight-line distance times the smallest current edge
cost per straight-line edge length, giving a consistent lower bound. Zero is a
safe fallback. The knapsack recurrence chooses the better of skipping an item
and taking it when its integer cost fits; reconstruction walks the table back.
Greedy processes positive-benefit zero-cost items first and otherwise uses
benefit-to-cost ratio with ID ties. The sample in the assignment and two further
counterexamples show why the greedy result is not guaranteed optimal.

Kruskal sorts undirected edges and joins distinct components. The generated
backbone receives extra roads for a lap and alternative routes. Backtracking
places consecutive checkpoints on adjacent ring positions, two spaced service
vertices, and two obstacles on edge-disjoint non-bridge roads outside the main
lap. These constraints prune invalid placements but restrict generated layouts
to a ring-based family.
Heap events use trigger time, priority and insertion sequence. Cancelled events
are lazily ignored at extraction; overlapping effects have independent expiry.
Top-k heapifies all entries before extraction, using O(n) space and
O(n + k log n) time. Quick Sort uses a middle-element pivot and three-way
partition. All ranking methods use the same total comparator.

## Verification

The automated tests currently cover traversal, route optimality comparisons,
heap operations, knapsack against exhaustive search, refuelling feasibility,
sort agreement, event cancellation and overlapping effects, three authored
circuits, deterministic races and a complete simulated championship. The latest
test run is recorded in `docs/testing/verification.md`; the suite should be
rerun against the final submission. Headless rendering checks are not a human
playthrough.

## Experimental studies

The five studies and the environment, generated inputs, raw samples, tables,
interpretation and limitations are documented in `experiments/results/analysis.md`
and `experiments/results/studies.json`. The companion analysis is included
after this report. Measurements are empirical for one machine and are not proof
of asymptotic complexity.

## Limitations and remaining submission work

The prototype needs further review against all assignment requirements, broader
generation and validation constraints, and human end-to-end play testing. The Windows build command produced
an executable, but the available host blocked launching it with Application
Control; successful execution is therefore not verified. Finalize and inspect
the executable, report and extracted submission ZIP on an allowed machine.
Add the actual group names, registration numbers and section. Do not treat
unfinished features or unverified packaging as complete.

## Acknowledgements

The project uses Python, Pygame, pytest, Matplotlib, and optional PyInstaller and
ReportLab. Its prototype graphics are drawn in code. Attribute any third-party
art, fonts or audio added later according to their licenses.
