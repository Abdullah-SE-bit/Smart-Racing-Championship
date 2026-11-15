# Experimental studies - measured prototype results

These are actual measurements from the current implementation, not projected results. Rerun `python experiments/benchmarks/run_studies.py` from the repository root to regenerate this file and `studies.json`.

Environment: Windows-11-10.0.26300-SP0; Intel64 Family 6 Model 142 Stepping 10, GenuineIntel; Python 3.12.16 (main, Oct 26 2026, 14:10:56) [MSC v.1944 64 bit (AMD64)]. Dependency versions: {'smart-racing-championship': '0.0.0', 'pygame': '2.6.1', 'pytest': '9.2.0', 'matplotlib': '3.11.2'}. Seed: 20261205. Each timing has one warm-up and 5 measured repetitions; values below are means in milliseconds. Raw samples and medians are in `studies.json`. perf_counter; milliseconds; one warm-up; algorithm initialization included except prepared event extraction; input generation, correctness checks, I/O and rendering excluded.

## 1. BFS and DFS

Objective: compare traversal time and work as graph size and density vary. Inputs are seeded connected undirected graphs with a chain and extra sparse or denser roads. The script checks reachability, BFS minimum-edge paths against an independent repeated-relaxation reference, weak components and cycle presence outside timed regions.

| Vertices | Edges | Density | Algorithm | Visited | Examined roads | Mean ms |
| ---: | ---: | --- | --- | ---: | ---: | ---: |
| 20 | 31 | sparse | bfs | 20 | 62 | 0.0414 |
| 20 | 31 | sparse | dfs | 20 | 62 | 0.0551 |
| 20 | 34 | denser | bfs | 20 | 68 | 0.0444 |
| 20 | 34 | denser | dfs | 20 | 68 | 0.0484 |
| 60 | 116 | sparse | bfs | 60 | 232 | 0.1241 |
| 60 | 116 | sparse | dfs | 60 | 232 | 0.1549 |
| 60 | 249 | denser | bfs | 60 | 498 | 0.2546 |
| 60 | 249 | denser | dfs | 60 | 498 | 0.3424 |
| 120 | 240 | sparse | bfs | 120 | 480 | 0.3365 |
| 120 | 240 | sparse | dfs | 120 | 480 | 0.3112 |
| 120 | 953 | denser | bfs | 120 | 1906 | 0.7630 |
| 120 | 953 | denser | dfs | 120 | 1906 | 2.4816 |

Both traversals visit all vertices in these connected inputs. Examined road counts depend on adjacency entries, including both directions of undirected roads. The small sizes, trace collection and machine noise limit timing conclusions; theoretical time remains O(V+E).

## 2. Dijkstra and A*

Objective: compare optimal routing on identical seeded sparse graphs with non-negative normalized costs. Coordinates are randomly generated and road costs need not equal geometric length. The heuristic uses the minimum edge cost per geometric unit. The script checks equal final costs outside timed regions.

| Vertices | Edges | Algorithm | Cost | Expanded | Relaxed | Heap operations | Mean ms |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 20 | 31 | dijkstra | 1.5391 | 14 | 41 | 33 | 0.4097 |
| 20 | 31 | astar | 1.5391 | 14 | 41 | 33 | 0.3180 |
| 60 | 116 | dijkstra | 1.0050 | 24 | 104 | 77 | 0.4895 |
| 60 | 116 | astar | 1.0050 | 23 | 97 | 75 | 0.4186 |
| 120 | 240 | dijkstra | 1.2432 | 67 | 279 | 208 | 1.2944 |
| 120 | 240 | astar | 1.2432 | 64 | 268 | 201 | 1.1607 |

A* expanded fewer vertices in 2 inputs, equal numbers in 1, and more in 0. Unobserved cases are not evidence that they cannot occur. Equal optimal costs are verified for each paired input. The heuristic may be weak, and its setup is timed, so A* need not be faster or expand fewer vertices in every case. These instances alone do not establish general performance.

## 3. Dynamic programming and greedy

Objective: compare 0/1 pickup benefit and runtime as item count and budget vary. Seeded item costs and benefits are generated before timing. Three small counterexamples are separately checked against exhaustive search.

| Items | Budget | Method | Benefit | DP states | Mean ms |
| ---: | ---: | --- | ---: | ---: | ---: |
| 10 | 30 | dp | 109 | 310 | 0.1128 |
| 10 | 30 | greedy | 109 | 0 | 0.1278 |
| 30 | 60 | dp | 252 | 1830 | 0.6089 |
| 30 | 60 | greedy | 252 | 0 | 0.5871 |
| 60 | 100 | dp | 551 | 6060 | 2.6049 |
| 60 | 100 | greedy | 550 | 0 | 2.4005 |

Counterexamples (budget, DP benefit, greedy benefit): (10, 48, 30); (6, 16, 12); (8, 30, 20). The selected IDs and input cases are saved in the raw JSON. DP is pseudo-polynomial in budget; greedy is feasible but need not be optimal. These small instances do not establish the performance of larger multi-resource planners.

## 4. Event priority queue

Objective: measure insertion/cancellation and extraction separately for seeded event queues. Inputs contain tied timestamps and priorities; every eleventh event is lazily cancelled. The result order is checked against time, priority and insertion sequence. Independent effect expiration is exercised by the automated race tests.

| Events | Cancelled | Heap operations | Insert + cancel ms | Extraction ms |
| ---: | ---: | ---: | ---: | ---: |
| 50 | 5 | 100 | 0.5366 | 0.2341 |
| 250 | 23 | 500 | 1.4300 | 1.4783 |
| 1000 | 91 | 2000 | 5.9894 | 7.3193 |

Extraction timing excludes preparing the queue; insertion includes queue creation. Lazy cancellation keeps entries in memory until extraction, so the benchmark reports operations for cancelled entries as well.

## 5. Sorting and top-k

Objective: compare the three manual sorts and heap top-k using the actual championship total comparator. Inputs are random, sorted, reversed and duplicate-heavy records. Each full result and top-k prefix is checked against the same reference order.

| Records | Input | Method | k | Mean ms |
| ---: | --- | --- | ---: | ---: |
| 50 | random | merge | - | 0.1872 |
| 50 | random | quick | - | 0.1444 |
| 50 | random | heap | - | 0.2774 |
| 50 | random | top_k | 5 | 0.0570 |
| 50 | random | top_k | 49 | 0.1468 |
| 50 | sorted | merge | - | 0.1643 |
| 50 | sorted | quick | - | 0.1664 |
| 50 | sorted | heap | - | 0.4406 |
| 50 | sorted | top_k | 5 | 0.0629 |
| 50 | sorted | top_k | 49 | 0.1376 |
| 50 | reverse | merge | - | 0.1529 |
| 50 | reverse | quick | - | 0.1031 |
| 50 | reverse | heap | - | 0.2338 |
| 50 | reverse | top_k | 5 | 0.0548 |
| 50 | reverse | top_k | 49 | 0.2428 |
| 50 | duplicates | merge | - | 0.1931 |
| 50 | duplicates | quick | - | 0.1508 |
| 50 | duplicates | heap | - | 0.2467 |
| 50 | duplicates | top_k | 5 | 0.0698 |
| 50 | duplicates | top_k | 49 | 0.2260 |
| 200 | random | merge | - | 1.1080 |
| 200 | random | quick | - | 1.0105 |
| 200 | random | heap | - | 1.6562 |
| 200 | random | top_k | 5 | 0.2160 |
| 200 | random | top_k | 199 | 0.8790 |
| 200 | sorted | merge | - | 0.7768 |
| 200 | sorted | quick | - | 0.5436 |
| 200 | sorted | heap | - | 2.0631 |
| 200 | sorted | top_k | 5 | 0.1460 |
| 200 | sorted | top_k | 199 | 0.7755 |
| 200 | reverse | merge | - | 0.7952 |
| 200 | reverse | quick | - | 0.5243 |
| 200 | reverse | heap | - | 1.5118 |
| 200 | reverse | top_k | 5 | 0.2002 |
| 200 | reverse | top_k | 199 | 1.2066 |
| 200 | duplicates | merge | - | 1.0349 |
| 200 | duplicates | quick | - | 2.1610 |
| 200 | duplicates | heap | - | 2.0593 |
| 200 | duplicates | top_k | 5 | 0.1823 |
| 200 | duplicates | top_k | 199 | 0.7435 |
| 500 | random | merge | - | 3.4774 |
| 500 | random | quick | - | 2.6895 |
| 500 | random | heap | - | 7.9237 |
| 500 | random | top_k | 5 | 0.7368 |
| 500 | random | top_k | 499 | 2.6309 |
| 500 | sorted | merge | - | 2.5821 |
| 500 | sorted | quick | - | 1.6849 |
| 500 | sorted | heap | - | 5.7675 |
| 500 | sorted | top_k | 5 | 0.4018 |
| 500 | sorted | top_k | 499 | 2.5205 |
| 500 | reverse | merge | - | 1.7955 |
| 500 | reverse | quick | - | 1.9244 |
| 500 | reverse | heap | - | 5.6763 |
| 500 | reverse | top_k | 5 | 0.7544 |
| 500 | reverse | top_k | 499 | 3.4475 |
| 500 | duplicates | merge | - | 4.4512 |
| 500 | duplicates | quick | - | 15.0919 |
| 500 | duplicates | heap | - | 4.9745 |
| 500 | duplicates | top_k | 5 | 0.4966 |
| 500 | duplicates | top_k | 499 | 2.2376 |

Top-k uses bottom-up heap construction followed by k extractions: O(n + k log n), with O(n) storage. Full sorting and retrieval have different output sizes, so comparisons should consider k relative to n. These measurements include comparator and heap setup; comparison counters are not currently instrumented.
