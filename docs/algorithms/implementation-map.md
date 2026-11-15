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

The explorer's alternatives view uses the shared DFS-style simple-path search.
It displays up to five routes other than the selected optimum and bounds the
search to 10,000 states and 16 vertices per path. These limits keep interactive
search responsive; because enumerating simple paths can be exponential, the UI
reports when a bound is reached and the result may be incomplete. Parallel roads
produce one vertex sequence, displayed using the cheapest available road for the
selected cost profile. This view compares endpoints and does not enforce the
checkpoint order required by an ordered lap.
