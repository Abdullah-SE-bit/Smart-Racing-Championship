# Experimental studies - measured prototype results

These are actual measurements from the current implementation, not projected results. Rerun `python experiments/benchmarks/run_studies.py` from the repository root to regenerate this file and `studies.json`.

Environment: Windows-11-10.0.26300-SP0; Intel64 Family 6 Model 142 Stepping 10, GenuineIntel; Python 3.12.16 (main, Oct 26 2026, 14:10:56) [MSC v.1944 64 bit (AMD64)]. Dependency versions: {'smart-racing-championship': '0.0.0', 'pygame': '2.6.1', 'pytest': '9.2.0', 'matplotlib': '3.11.2'}. Seed: 20261205. Each timing has one warm-up and 5 measured repetitions; values below are means in milliseconds. Raw samples and medians are in `studies.json`. perf_counter; milliseconds; one warm-up; algorithm initialization included except prepared event extraction; input generation, correctness checks, I/O and rendering excluded.

## 1. BFS and DFS

Objective: compare traversal time and work as graph size and density vary. Inputs are seeded connected undirected graphs with a chain and extra sparse or denser roads. The script checks reachability, BFS minimum-edge paths against an independent repeated-relaxation reference, weak components and cycle presence outside timed regions.

| Vertices | Edges | Density | Algorithm | Visited | Examined roads | Mean ms |
| ---: | ---: | --- | --- | ---: | ---: | ---: |
| 20 | 31 | sparse | bfs | 20 | 62 | 0.0854 |
| 20 | 31 | sparse | dfs | 20 | 62 | 0.0857 |
| 20 | 34 | denser | bfs | 20 | 68 | 0.0514 |
| 20 | 34 | denser | dfs | 20 | 68 | 0.0710 |
| 60 | 116 | sparse | bfs | 60 | 232 | 0.0873 |
| 60 | 116 | sparse | dfs | 60 | 232 | 0.1201 |
| 60 | 249 | denser | bfs | 60 | 498 | 0.1670 |
| 60 | 249 | denser | dfs | 60 | 498 | 0.5595 |
| 120 | 240 | sparse | bfs | 120 | 480 | 0.4181 |
| 120 | 240 | sparse | dfs | 120 | 480 | 0.5507 |
| 120 | 953 | denser | bfs | 120 | 1906 | 1.2392 |
| 120 | 953 | denser | dfs | 120 | 1906 | 1.7774 |

Both traversals visit all vertices in these connected inputs. Examined road counts depend on adjacency entries, including both directions of undirected roads. The small sizes, trace collection and machine noise limit timing conclusions; theoretical time remains O(V+E).

## 2. Dijkstra and A*

Objective: compare optimal routing on identical seeded sparse graphs with non-negative normalized costs. Coordinates are randomly generated and road costs need not equal geometric length. The heuristic uses the minimum edge cost per geometric unit. The script checks equal final costs outside timed regions. Routing heap operations count insertions, priority decreases and extractions.

| Vertices | Edges | Algorithm | Cost | Expanded | Relaxed | Heap operations | Mean ms |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 20 | 31 | dijkstra | 1.5391 | 14 | 41 | 33 | 0.2220 |
| 20 | 31 | astar | 1.5391 | 14 | 41 | 33 | 0.1497 |
| 60 | 116 | dijkstra | 1.0050 | 24 | 104 | 77 | 0.8775 |
| 60 | 116 | astar | 1.0050 | 23 | 97 | 75 | 0.9963 |
| 120 | 240 | dijkstra | 1.2432 | 67 | 279 | 205 | 0.7091 |
| 120 | 240 | astar | 1.2432 | 64 | 268 | 199 | 0.9989 |

A* expanded fewer vertices in 2 inputs, equal numbers in 1, and more in 0. Unobserved cases are not evidence that they cannot occur. Equal optimal costs are verified for each paired input. The heuristic may be weak, and its setup is timed, so A* need not be faster or expand fewer vertices in every case. These instances alone do not establish general performance.

## 3. Dynamic programming and greedy

Objective: compare 0/1 pickup benefit and runtime as item count and budget vary. All cases, including the assignment example and two team counterexamples, are timed. Each counterexample is checked against exhaustive search before timing.

| Items | Budget | Method | Benefit | DP states | Mean ms |
| ---: | ---: | --- | ---: | ---: | ---: |
| 3 | 10 | dp | 48 | 33 | 0.0111 |
| 3 | 10 | greedy | 30 | 0 | 0.0126 |
| 3 | 6 | dp | 16 | 21 | 0.0086 |
| 3 | 6 | greedy | 12 | 0 | 0.0124 |
| 3 | 8 | dp | 30 | 27 | 0.0099 |
| 3 | 8 | greedy | 20 | 0 | 0.0122 |
| 10 | 30 | dp | 109 | 310 | 0.0936 |
| 10 | 30 | greedy | 109 | 0 | 0.1688 |
| 30 | 60 | dp | 252 | 1830 | 0.6188 |
| 30 | 60 | greedy | 252 | 0 | 0.5724 |
| 60 | 100 | dp | 551 | 6060 | 2.1207 |
| 60 | 100 | greedy | 550 | 0 | 1.8967 |

Counterexamples (budget, DP benefit, greedy benefit): (10, 48, 30); (6, 16, 12); (8, 30, 20). The selected IDs and input cases are saved in the raw JSON. DP is pseudo-polynomial in budget; greedy is feasible but need not be optimal. These small instances do not establish the performance of larger multi-resource planners.

## 4. Event priority queue

Objective: measure insertion and extraction separately for seeded queues. Timestamps and priorities include ties. Before extraction, every eleventh event is lazily cancelled. The reference order uses trigger time, priority and insertion sequence. In a separate race check, two closures start at t=1. The road stays blocked after one expires at t=3 and opens at t=6. The raw results record the surviving effects at each time.

| Events | Cancelled | Heap operations | Insertion ms | Extraction ms |
| ---: | ---: | ---: | ---: | ---: |
| 50 | 5 | 100 | 0.2537 | 0.1097 |
| 250 | 23 | 500 | 1.1516 | 1.2558 |
| 1000 | 91 | 2000 | 8.7200 | 10.3616 |

Extraction timing excludes preparing the queue; insertion includes queue creation. Lazy cancellation keeps entries in memory until extraction, so the benchmark reports operations for cancelled entries as well.

## 5. Sorting and top-k

Objective: compare the three manual sorts and heap top-k using the actual championship total comparator. Inputs are random, sorted, reversed and duplicate-heavy records. Each full result and top-k prefix is checked against the same reference order.

| Records | Input | Method | k | Mean ms |
| ---: | --- | --- | ---: | ---: |
| 50 | random | merge | - | 0.1757 |
| 50 | random | quick | - | 0.1148 |
| 50 | random | heap | - | 1.6131 |
| 50 | random | top_k | 5 | 0.0775 |
| 50 | random | top_k | 49 | 0.2142 |
| 50 | sorted | merge | - | 0.1216 |
| 50 | sorted | quick | - | 0.0860 |
| 50 | sorted | heap | - | 0.2163 |
| 50 | sorted | top_k | 5 | 0.0304 |
| 50 | sorted | top_k | 49 | 0.2238 |
| 50 | reverse | merge | - | 0.1258 |
| 50 | reverse | quick | - | 0.2579 |
| 50 | reverse | heap | - | 0.3809 |
| 50 | reverse | top_k | 5 | 0.2567 |
| 50 | reverse | top_k | 49 | 0.2541 |
| 50 | duplicates | merge | - | 0.1679 |
| 50 | duplicates | quick | - | 0.1293 |
| 50 | duplicates | heap | - | 0.2122 |
| 50 | duplicates | top_k | 5 | 0.0517 |
| 50 | duplicates | top_k | 49 | 0.2244 |
| 200 | random | merge | - | 1.0563 |
| 200 | random | quick | - | 0.6943 |
| 200 | random | heap | - | 2.4763 |
| 200 | random | top_k | 5 | 0.1453 |
| 200 | random | top_k | 199 | 2.5712 |
| 200 | sorted | merge | - | 0.6337 |
| 200 | sorted | quick | - | 0.6545 |
| 200 | sorted | heap | - | 1.4312 |
| 200 | sorted | top_k | 5 | 0.1117 |
| 200 | sorted | top_k | 199 | 2.4077 |
| 200 | reverse | merge | - | 0.8557 |
| 200 | reverse | quick | - | 0.4508 |
| 200 | reverse | heap | - | 1.5654 |
| 200 | reverse | top_k | 5 | 0.5497 |
| 200 | reverse | top_k | 199 | 1.4194 |
| 200 | duplicates | merge | - | 0.9302 |
| 200 | duplicates | quick | - | 2.5030 |
| 200 | duplicates | heap | - | 2.0963 |
| 200 | duplicates | top_k | 5 | 0.2779 |
| 200 | duplicates | top_k | 199 | 2.9274 |
| 500 | random | merge | - | 11.4913 |
| 500 | random | quick | - | 7.2566 |
| 500 | random | heap | - | 8.9389 |
| 500 | random | top_k | 5 | 0.3375 |
| 500 | random | top_k | 499 | 4.1434 |
| 500 | sorted | merge | - | 1.8984 |
| 500 | sorted | quick | - | 1.4751 |
| 500 | sorted | heap | - | 5.9862 |
| 500 | sorted | top_k | 5 | 0.2572 |
| 500 | sorted | top_k | 499 | 5.2343 |
| 500 | reverse | merge | - | 1.8585 |
| 500 | reverse | quick | - | 1.2885 |
| 500 | reverse | heap | - | 4.8568 |
| 500 | reverse | top_k | 5 | 1.3139 |
| 500 | reverse | top_k | 499 | 4.0176 |
| 500 | duplicates | merge | - | 2.5931 |
| 500 | duplicates | quick | - | 8.2048 |
| 500 | duplicates | heap | - | 4.8666 |
| 500 | duplicates | top_k | 5 | 0.2339 |
| 500 | duplicates | top_k | 499 | 3.7921 |

For 500 random records, the bounded heap averaged 0.3375 ms for k=5 and 4.1434 ms for k=499. Merge Sort ranked the entire field in 11.4913 ms. The heap retains at most k entries and runs in O(n log(k+1)) time with O(k) storage. As k approaches n, its memory and extraction costs approach those of a full ranking. These timings include comparator and heap setup and depend on the input order and machine.
