# Experimental studies - measured prototype results

These are actual measurements from the current implementation, not projected results. Rerun `python experiments/benchmarks/run_studies.py` from the repository root to regenerate this file and `studies.json`.

Environment: Windows-11-10.0.26300-SP0; Intel64 Family 6 Model 142 Stepping 10, GenuineIntel; Python 3.12.16 (main, Oct 26 2026, 14:10:56) [MSC v.1944 64 bit (AMD64)]. Dependency versions: {'smart-racing-championship': '0.0.0', 'pygame': '2.6.1', 'pytest': '9.2.0', 'matplotlib': '3.11.2'}. Seed: 20261205. Each timing has one warm-up and 5 measured repetitions; values below are means in milliseconds. Raw samples and medians are in `studies.json`. perf_counter; milliseconds; one warm-up; algorithm initialization included except prepared event extraction; input generation, correctness checks, I/O and rendering excluded.

## 1. BFS and DFS

Objective: compare traversal time and work as graph size and density vary. Inputs are seeded connected undirected graphs with a chain and extra sparse or denser roads. The script checks reachability, BFS minimum-edge paths against an independent repeated-relaxation reference, weak components and cycle presence outside timed regions.

| Vertices | Edges | Density | Algorithm | Visited | Examined roads | Mean ms |
| ---: | ---: | --- | --- | ---: | ---: | ---: |
| 20 | 31 | sparse | bfs | 20 | 62 | 0.0259 |
| 20 | 31 | sparse | dfs | 20 | 62 | 0.0344 |
| 20 | 34 | denser | bfs | 20 | 68 | 0.0264 |
| 20 | 34 | denser | dfs | 20 | 68 | 0.0360 |
| 60 | 116 | sparse | bfs | 60 | 232 | 0.0856 |
| 60 | 116 | sparse | dfs | 60 | 232 | 0.1144 |
| 60 | 249 | denser | bfs | 60 | 498 | 0.1514 |
| 60 | 249 | denser | dfs | 60 | 498 | 0.2157 |
| 120 | 240 | sparse | bfs | 120 | 480 | 0.2027 |
| 120 | 240 | sparse | dfs | 120 | 480 | 0.2865 |
| 120 | 953 | denser | bfs | 120 | 1906 | 0.5035 |
| 120 | 953 | denser | dfs | 120 | 1906 | 0.8433 |

Both traversals visit all vertices in these connected inputs. Examined road counts depend on adjacency entries, including both directions of undirected roads. The small sizes, trace collection and machine noise limit timing conclusions; theoretical time remains O(V+E).

## 2. Dijkstra and A*

Objective: compare optimal routing on identical seeded sparse graphs with non-negative normalized costs. Coordinates are randomly generated and road costs need not equal geometric length. The heuristic uses the minimum edge cost per geometric unit. The script checks equal final costs outside timed regions. Routing heap operations count insertions, priority decreases and extractions.

| Vertices | Edges | Algorithm | Cost | Expanded | Relaxed | Heap operations | Mean ms |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 20 | 31 | dijkstra | 1.5391 | 14 | 41 | 33 | 0.1383 |
| 20 | 31 | astar | 1.5391 | 14 | 41 | 33 | 0.1208 |
| 60 | 116 | dijkstra | 1.0050 | 24 | 104 | 77 | 0.3402 |
| 60 | 116 | astar | 1.0050 | 23 | 97 | 75 | 0.3296 |
| 120 | 240 | dijkstra | 1.2432 | 67 | 279 | 205 | 0.8635 |
| 120 | 240 | astar | 1.2432 | 64 | 268 | 199 | 1.3850 |

A* expanded fewer vertices in 2 inputs, equal numbers in 1, and more in 0. Unobserved cases are not evidence that they cannot occur. Equal optimal costs are verified for each paired input. The heuristic may be weak, and its setup is timed, so A* need not be faster or expand fewer vertices in every case. These instances alone do not establish general performance.

## 3. Dynamic programming and greedy

Objective: compare 0/1 pickup benefit and runtime as item count and budget vary. Seeded item costs and benefits are generated before timing. Three small counterexamples are separately checked against exhaustive search.

| Items | Budget | Method | Benefit | DP states | Mean ms |
| ---: | ---: | --- | ---: | ---: | ---: |
| 10 | 30 | dp | 109 | 310 | 0.0800 |
| 10 | 30 | greedy | 109 | 0 | 0.0892 |
| 30 | 60 | dp | 252 | 1830 | 0.4843 |
| 30 | 60 | greedy | 252 | 0 | 0.4622 |
| 60 | 100 | dp | 551 | 6060 | 2.0178 |
| 60 | 100 | greedy | 550 | 0 | 1.5573 |

Counterexamples (budget, DP benefit, greedy benefit): (10, 48, 30); (6, 16, 12); (8, 30, 20). The selected IDs and input cases are saved in the raw JSON. DP is pseudo-polynomial in budget; greedy is feasible but need not be optimal. These small instances do not establish the performance of larger multi-resource planners.

## 4. Event priority queue

Objective: measure insertion/cancellation and extraction separately for seeded event queues. Inputs contain tied timestamps and priorities; every eleventh event is lazily cancelled. The result order is checked against time, priority and insertion sequence. Independent effect expiration is exercised by the automated race tests.

| Events | Cancelled | Heap operations | Insert + cancel ms | Extraction ms |
| ---: | ---: | ---: | ---: | ---: |
| 50 | 5 | 100 | 0.1874 | 0.0904 |
| 250 | 23 | 500 | 1.8598 | 0.8939 |
| 1000 | 91 | 2000 | 6.4063 | 5.0008 |

Extraction timing excludes preparing the queue; insertion includes queue creation. Lazy cancellation keeps entries in memory until extraction, so the benchmark reports operations for cancelled entries as well.

## 5. Sorting and top-k

Objective: compare the three manual sorts and heap top-k using the actual championship total comparator. Inputs are random, sorted, reversed and duplicate-heavy records. Each full result and top-k prefix is checked against the same reference order.

| Records | Input | Method | k | Mean ms |
| ---: | --- | --- | ---: | ---: |
| 50 | random | merge | - | 0.1762 |
| 50 | random | quick | - | 0.1147 |
| 50 | random | heap | - | 0.2126 |
| 50 | random | top_k | 5 | 0.0450 |
| 50 | random | top_k | 49 | 0.1135 |
| 50 | sorted | merge | - | 0.1818 |
| 50 | sorted | quick | - | 0.3705 |
| 50 | sorted | heap | - | 0.6143 |
| 50 | sorted | top_k | 5 | 0.0887 |
| 50 | sorted | top_k | 49 | 0.2305 |
| 50 | reverse | merge | - | 0.1293 |
| 50 | reverse | quick | - | 0.0870 |
| 50 | reverse | heap | - | 0.1932 |
| 50 | reverse | top_k | 5 | 0.0474 |
| 50 | reverse | top_k | 49 | 0.1418 |
| 50 | duplicates | merge | - | 0.1612 |
| 50 | duplicates | quick | - | 0.1762 |
| 50 | duplicates | heap | - | 0.6450 |
| 50 | duplicates | top_k | 5 | 0.1173 |
| 50 | duplicates | top_k | 49 | 0.2774 |
| 200 | random | merge | - | 0.8621 |
| 200 | random | quick | - | 1.1197 |
| 200 | random | heap | - | 1.6706 |
| 200 | random | top_k | 5 | 0.3190 |
| 200 | random | top_k | 199 | 1.0526 |
| 200 | sorted | merge | - | 1.4929 |
| 200 | sorted | quick | - | 0.4423 |
| 200 | sorted | heap | - | 2.3338 |
| 200 | sorted | top_k | 5 | 0.2015 |
| 200 | sorted | top_k | 199 | 0.6054 |
| 200 | reverse | merge | - | 1.3821 |
| 200 | reverse | quick | - | 0.5046 |
| 200 | reverse | heap | - | 1.7789 |
| 200 | reverse | top_k | 5 | 0.1594 |
| 200 | reverse | top_k | 199 | 0.5998 |
| 200 | duplicates | merge | - | 0.7600 |
| 200 | duplicates | quick | - | 1.2000 |
| 200 | duplicates | heap | - | 1.5750 |
| 200 | duplicates | top_k | 5 | 0.3938 |
| 200 | duplicates | top_k | 199 | 0.5935 |
| 500 | random | merge | - | 3.0310 |
| 500 | random | quick | - | 1.8949 |
| 500 | random | heap | - | 4.3183 |
| 500 | random | top_k | 5 | 0.4615 |
| 500 | random | top_k | 499 | 2.8079 |
| 500 | sorted | merge | - | 2.0280 |
| 500 | sorted | quick | - | 1.2746 |
| 500 | sorted | heap | - | 4.6860 |
| 500 | sorted | top_k | 5 | 0.2881 |
| 500 | sorted | top_k | 499 | 1.9305 |
| 500 | reverse | merge | - | 1.7302 |
| 500 | reverse | quick | - | 1.6841 |
| 500 | reverse | heap | - | 3.7947 |
| 500 | reverse | top_k | 5 | 0.6029 |
| 500 | reverse | top_k | 499 | 2.0091 |
| 500 | duplicates | merge | - | 2.7916 |
| 500 | duplicates | quick | - | 6.7443 |
| 500 | duplicates | heap | - | 4.1315 |
| 500 | duplicates | top_k | 5 | 0.5257 |
| 500 | duplicates | top_k | 499 | 1.9317 |

Top-k uses bottom-up heap construction followed by k extractions: O(n + k log n), with O(n) storage. Full sorting and retrieval have different output sizes, so comparisons should consider k relative to n. These measurements include comparator and heap setup; comparison counters are not currently instrumented.
