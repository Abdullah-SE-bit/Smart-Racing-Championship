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

## Route-cost normalization

For an edge e, the optimized cost is
`wd * distance/100 + wt * effectiveTime/10 + wf * adjustedFuel/10 +
wr * (difficulty - 1)/4 + wo * obstacle/1`. Effective time is base time
multiplied by 1.5 when the edge is restricted; adjusted fuel is base fuel
multiplied by `1 + 0.1 * (difficulty - 1)`. The reference values are fixed
scales for the circuit data, so all five terms are non-negative before
weighting. The displayed cost is the same sum optimized by the router.

| Preset | Distance | Time | Fuel | Difficulty | Obstacle |
| --- | ---: | ---: | ---: | ---: | ---: |
| Balanced | 1 | 1 | 1 | 1 | 1 |
| Speed | 0.2 | 3 | 0.2 | 0.2 | 0.3 |
| Economy | 0.3 | 0.2 | 3 | 0.3 | 0.2 |
| Safety | 0.3 | 0.3 | 0.3 | 3 | 3 |

The speed, economy and safety profiles prioritize their named objective;
balanced weights give every normalized term the same multiplier. These are
design choices, not measurements of the relative value of different units.
Changing reference values or weights can change the selected route, and one
scalar score cannot represent all possible trade-offs.

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

## Pseudocode and correctness arguments

**BFS.** Set the start parent to none and enqueue it. While the queue is not
empty, remove its front vertex; for each open outgoing road, record the parent
and enqueue an undiscovered neighbor. The FIFO queue visits vertices in
nondecreasing edge count, so the first parent chain found for a vertex has the
minimum number of roads. The explorer uses the resulting parents and trace.

**DFS and bounded alternatives.** Mark the start, then repeatedly follow an
unvisited outgoing neighbor, recording its parent; backtrack when a vertex has
no remaining neighbors. A visited set prevents infinite traversal of cycles.
Separate graph helpers test cycles, weak components and dead ends. Alternative
paths backtrack over vertices already on the current path and stop at explicit
state, path-count and length limits. A limited search can be incomplete; a
single traversal is linear, while simple-path enumeration may be exponential.

**Dijkstra.** Set the start distance to zero, push it into a min-heap, and
repeatedly extract the least tentative distance. For each legal outgoing road,
relax the destination and push an improved value; ignore stale heap entries.
With non-negative costs, the first current extraction of the destination has
optimal cost. Parent roads reconstruct the path; blocked roads are excluded.

**A-star.** Use the same relaxation and parents, but order the heap by the sum
of tentative cost and a geometric lower bound to the target. The minimum current
edge-cost-to-geometric-length ratio makes this bound consistent; zero is a safe
fallback. Therefore a current target extraction is optimal under the same
non-negative cost assumption. Ordered laps run separate searches for each next
checkpoint while excluding later checkpoints from each leg.

**Knapsack DP.** For each pickup and budget, store the better value between
skipping it and taking it if its integer cost fits. Begin with an all-zero row,
then walk the completed table backwards to recover chosen items. Each row uses
only the previous row, so every item is used at most once and induction on the
number of items gives the optimal benefit for each budget. Runtime and storage
are O(mB), where B is the numeric budget, not its bit length.

**Refuelling DP.** Map each reachable discrete fuel amount to its smallest
accumulated stop time and purchase history. At each route vertex, try permitted
purchases, subtract the next edge's requirement, and retain the best history
for each arrival fuel. A state records everything needed for later transitions,
so discarding a slower history with the same fuel preserves an optimal plan.
Fuel is discretized in tenths with conservative rounding; the race engine fills
up to 40 units at the same fixed stop time. This can leave more fuel than the
minimum DP purchase without invalidating the plan. The planner displays the
station vertices and planned quantities for the selected route; pickup advice
for an ordered lap respects its checkpoint sequence and nitro capacity.

**Greedy pickup choice.** Process positive-benefit zero-cost items first, then
consider the remaining items in descending exact benefit-to-cost ratio with ID
ties. Select an item only if it fits the remaining scalar detour budget. The
result is feasible but not always optimal: the supplied budget-10 case produces
benefit 30 versus the DP optimum of 48. The study includes two further checked
counterexamples.

**Backtracking and Kruskal.** The generator attempts candidate placements,
rejects choices that violate spacing or route constraints, and backtracks when a
partial placement cannot be completed. It accepts a candidate only after circuit
validation, with bounded retries. Kruskal sorts undirected candidate roads by
weight and adds an edge only when union-find places its endpoints in different
components. The cut property yields a minimum spanning forest; connected
candidates yield a spanning tree. Extra roads supply laps and alternatives.

**Binary heap and event queue.** Insert by appending and sifting upward; remove
the root by moving the last element to the root and sifting downward. These
operations preserve the parent-before-children invariant. Event keys include
trigger time, priority and insertion sequence, so extracting the minimum gives
the specified deterministic order. Cancellation is lazy and temporary effects
have independent expiration events.

**Merge Sort.** Recursively split the entries, sort each half, and merge by the
shared championship key. Both halves are sorted by induction, and repeatedly
choosing their smallest front entry produces the sorted result. Its O(n log n)
work uses O(n) additional storage for merging.

**Quick Sort.** Choose the middle entry's key as pivot, partition entries into
lower, equal and greater groups, then recursively sort and concatenate the
outer groups. Each partition preserves all entries and places every lower key
before every greater key, so induction gives a sorted result. Work averages
O(n log n) but can be O(n^2); the lists used by this implementation take space.

**Heap Sort and top-k.** Heap Sort builds a max-heap, repeatedly swaps its
root with the final unsorted position, then restores the heap invariant. Each
extraction fixes the greatest remaining key at the end. Top-k instead heapifies
the shared championship keys in a min-heap and extracts k entries. Its output
is the first k entries of the same total ordering, using O(n + k log n) time
and O(n) storage. The studies compare this with all three full sorts.

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

## Advanced challenges and observed checks

Generated circuits use a seeded Kruskal backbone and bounded backtracking. A
separate local check generated and validated seeds 0 through 99; the automated
suite also completes races on five generated tracks. These checks do not prove
that every possible seed or layout will succeed. The generator retries invalid
candidates up to its documented limit, and the interface can save a valid track.

The balanced, speed, economy and safety profiles combine normalized non-negative
road attributes with different weights. An automated fixture confirms that
different presets choose different paths; scores from different profiles do not
share a common scale. The championship dashboard supports a selectable k and
the heap leaders use the same comparator as the three full sorting methods.
The fifth study records measured timings for small k and for k close to n.

## Limitations and remaining submission work

The prototype needs further review against all assignment requirements, broader
generation and validation constraints, and human end-to-end play testing. A
clean Windows CI runner built the executable and successfully launched its
headless smoke test. The local host blocked the virtual-environment Python and
the packaged executable with Application Control. A base Python runtime did
launch the game locally, but a complete human playthrough remains unverified.
Finalize and inspect the executable, report and extracted
submission ZIP on an allowed machine.
Add the actual group names, registration numbers and section. Do not treat
unfinished features or unverified packaging as complete.

## Conclusion

The prototype connects graph search, route optimization, resource planning,
event scheduling, track generation and championship ranking to a playable
racing workflow. The automated checks and five measured studies provide
evidence for the tested cases and show how the algorithms behave on the
recorded inputs. They do not establish correctness for every possible circuit
or replace a full human playthrough. Final requirement review, group details,
packaged-game verification and the demo and viva remain before submission.

## Acknowledgements

The project uses Python, Pygame, pytest, Matplotlib, and optional PyInstaller and
ReportLab; dependency declarations and version ranges are in `pyproject.toml`,
and the measured study environment records installed versions. Circuit data and
the prototype graphics are authored in this repository. The interface asks the
operating system for Segoe UI and does not distribute that font. No external art
or audio is included in the current prototype. Attribute any third-party art,
fonts or audio added later according to their licenses.

Reference material: the assignment transcription in `docs/assignment-specification.md`;
Python documentation at https://docs.python.org/3/; Pygame documentation at
https://pygame.org/docs; pytest documentation at https://docs.pytest.org/;
Matplotlib documentation at https://matplotlib.org/; PyInstaller documentation
at https://pyinstaller.org/; and ReportLab at https://www.reportlab.com/.
