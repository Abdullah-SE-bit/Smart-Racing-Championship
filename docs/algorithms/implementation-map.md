# Algorithm implementation map

The game, lab and studies import the functions listed here. Trace records are
plain Python data; rendering stays in `ui/`. See the assignment and report for
requirements and complexity details.

| Required family | Implementation | Current integration |
| --- | --- | --- |
| BFS | `algorithms/graph/traversal.py:bfs` | Explorer reachability, lab and study 1. |
| DFS | `algorithms/graph/traversal.py:dfs`, `has_cycle`, `weak_components`, `dead_ends`, `simple_paths` | Explorer, bounded alternatives, lab and study 1. |
| Dijkstra and A* | `algorithms/routing/shortest.py:shortest_path` | Route planner, checkpoint legs, opponent routing, lab and study 2. |
| Dynamic programming | `algorithms/optimization/resources.py:knapsack` and `refuel_plan` | Pickup recommendation, lab and study 3; refuelling planner is available as a separate fixed-route function. |
| Greedy | `algorithms/optimization/resources.py:greedy` | Pickup comparison, lab and study 3. |
| Backtracking | `tracks/generator.py:_assign_checkpoints`, `_place_obstacles` | Generated circuits and lab. |
| MST | `algorithms/generation/mst.py:kruskal` | Generated circuit backbone and lab. |
| Heap | `algorithms/structures/heap.py:MinHeap` | Routing, event scheduling, top-k, lab and studies 2, 4 and 5. |
| Merge, Quick and Heap Sort | `algorithms/sorting/rankings.py` | Championship ranking comparisons, lab and study 5. |

Routing's `relaxed` counter counts edge relaxation attempts, not only successful
distance updates. Traversal counts examined adjacency entries, so an undirected
road may be examined from both endpoints. Heap operations count insertions and
extractions; bottom-up heap construction is included in elapsed time but is not
counted as insertions. Experiment timing conventions are in the generated
`experiments/results/analysis.md`.

The Lab uses the selected circuit's reachable pickup suggestion for the DP and
greedy demonstrations and its road attributes for the heap example. Sorting
uses current championship entries when available and the selected circuit's
checkpoint IDs otherwise. Backtracking shows the generator's placement example
using the current checkpoint IDs. For Kruskal, the Lab applies the shared
implementation to the selected track's undirected roads and reports how many
one-way roads were excluded. It reports a disconnected undirected candidate
instead of displaying a forest as a spanning tree.

Merge Sort keeps the left entry first on equal keys, and this Quick Sort builds
stable lower/equal/greater partitions around the middle-element pivot; both
preserve input order for equal keys. Heap Sort can reorder equal keys. In the
championship, racer ID is the final tie-breaker, so distinct racers have distinct
total keys and every method produces the same order. Quick Sort averages
O(n log n) work but has O(n^2) worst-case work and uses partition lists.

The explorer's alternatives view uses the shared DFS-style simple-path search.
It displays up to five routes other than the selected optimum and bounds the
search to 10,000 states and 16 vertices per path. These limits keep interactive
search responsive; because enumerating simple paths can be exponential, the UI
reports when a bound is reached and the result may be incomplete. Parallel roads
produce one vertex sequence, displayed using the cheapest available road for the
selected cost profile. This view compares endpoints and does not enforce the
checkpoint order required by an ordered lap.

Mixed-graph cycle detection first traverses undirected roads, detecting a cycle
and assigning undirected connected components. A directed road inside one such
component closes a cycle. The remaining directed roads form a component graph,
on which a directed DFS detects cycles. This handles parallel directed and
undirected roads without counting the reverse traversal of a single undirected
road as a cycle. Both passes take O(V+E) time and O(V+E) auxiliary space.
