# Experimental studies - measured prototype results

These are actual measurements from the current implementation, not projected results. Rerun `python experiments/benchmarks/run_studies.py` from the repository root to regenerate this file and `studies.json`.

Environment: Windows-11-10.0.26300-SP0; Intel64 Family 6 Model 142 Stepping 10, GenuineIntel; Python 3.12.16 (main, Oct 26 2026, 14:10:56) [MSC v.1944 64 bit (AMD64)]. Dependency versions: {'smart-racing-championship': '0.0.0', 'pygame': '2.6.1', 'pytest': '9.2.0', 'matplotlib': '3.11.2'}. Seed: 20261205. Each timing has one warm-up and 5 measured repetitions; values below are means in milliseconds. Raw samples and medians are in `studies.json`. perf_counter; milliseconds; one warm-up; algorithm initialization included except prepared event extraction; input generation, correctness checks, I/O and rendering excluded.

## 1. BFS and DFS

Objective: compare traversal time and work as graph size and density vary. Inputs are seeded connected undirected graphs with a chain and extra sparse or denser roads. The script checks reachability, BFS minimum-edge paths against an independent repeated-relaxation reference, weak components and cycle presence outside timed regions.

| Vertices | Edges | Density | Algorithm | Visited | Examined roads | Mean ms |
| ---: | ---: | --- | --- | ---: | ---: | ---: |
| 20 | 31 | sparse | bfs | 20 | 62 | 0.0304 |
| 20 | 31 | sparse | dfs | 20 | 62 | 0.0399 |
| 20 | 34 | denser | bfs | 20 | 68 | 0.0911 |
| 20 | 34 | denser | dfs | 20 | 68 | 0.1463 |
| 60 | 116 | sparse | bfs | 60 | 232 | 0.1897 |
| 60 | 116 | sparse | dfs | 60 | 232 | 0.1488 |
| 60 | 249 | denser | bfs | 60 | 498 | 0.1731 |
| 60 | 249 | denser | dfs | 60 | 498 | 0.5303 |
| 120 | 240 | sparse | bfs | 120 | 480 | 0.6431 |
| 120 | 240 | sparse | dfs | 120 | 480 | 0.4489 |
| 120 | 953 | denser | bfs | 120 | 1906 | 0.9189 |
| 120 | 953 | denser | dfs | 120 | 1906 | 0.8449 |

Both traversals visit all vertices in these connected inputs. Examined road counts depend on adjacency entries, including both directions of undirected roads. The small sizes, trace collection and machine noise limit timing conclusions; theoretical time remains O(V+E).

## 2. Dijkstra and A*

Objective: compare optimal routing on identical seeded sparse graphs with non-negative normalized costs. Coordinates are randomly generated and road costs need not equal geometric length. The heuristic uses the minimum edge cost per geometric unit. The script checks equal final costs outside timed regions. Routing heap operations count insertions, priority decreases and extractions.

| Vertices | Edges | Algorithm | Cost | Expanded | Relaxed | Heap operations | Mean ms |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 20 | 31 | dijkstra | 1.5391 | 14 | 41 | 33 | 0.1437 |
| 20 | 31 | astar | 1.5391 | 14 | 41 | 33 | 0.3520 |
| 60 | 116 | dijkstra | 1.0050 | 24 | 104 | 77 | 0.5041 |
| 60 | 116 | astar | 1.0050 | 23 | 97 | 75 | 0.3877 |
| 120 | 240 | dijkstra | 1.2432 | 67 | 279 | 205 | 1.8794 |
| 120 | 240 | astar | 1.2432 | 64 | 268 | 199 | 2.7466 |

A* expanded fewer vertices in 2 inputs, equal numbers in 1, and more in 0. Unobserved cases are not evidence that they cannot occur. Equal optimal costs are verified for each paired input. The heuristic may be weak, and its setup is timed, so A* need not be faster or expand fewer vertices in every case. These instances alone do not establish general performance.

## 3. Dynamic programming and greedy

Objective: compare 0/1 pickup benefit and runtime as item count and budget vary. Seeded item costs and benefits are generated before timing. Three small counterexamples are separately checked against exhaustive search.

| Items | Budget | Method | Benefit | DP states | Mean ms |
| ---: | ---: | --- | ---: | ---: | ---: |
| 10 | 30 | dp | 109 | 310 | 0.0946 |
| 10 | 30 | greedy | 109 | 0 | 0.1197 |
| 30 | 60 | dp | 252 | 1830 | 0.7288 |
| 30 | 60 | greedy | 252 | 0 | 0.8144 |
| 60 | 100 | dp | 551 | 6060 | 2.6805 |
| 60 | 100 | greedy | 550 | 0 | 1.5662 |

Counterexamples (budget, DP benefit, greedy benefit): (10, 48, 30); (6, 16, 12); (8, 30, 20). The selected IDs and input cases are saved in the raw JSON. DP is pseudo-polynomial in budget; greedy is feasible but need not be optimal. These small instances do not establish the performance of larger multi-resource planners.

## 4. Event priority queue

Objective: measure insertion/cancellation and extraction separately for seeded event queues. Inputs contain tied timestamps and priorities; every eleventh event is lazily cancelled. The result order is checked against time, priority and insertion sequence. Independent effect expiration is exercised by the automated race tests.

| Events | Cancelled | Heap operations | Insert + cancel ms | Extraction ms |
| ---: | ---: | ---: | ---: | ---: |
| 50 | 5 | 100 | 0.2793 | 0.1114 |
| 250 | 23 | 500 | 1.6300 | 0.7934 |
| 1000 | 91 | 2000 | 7.4670 | 5.5967 |

Extraction timing excludes preparing the queue; insertion includes queue creation. Lazy cancellation keeps entries in memory until extraction, so the benchmark reports operations for cancelled entries as well.

## 5. Sorting and top-k

Objective: compare the three manual sorts and heap top-k using the actual championship total comparator. Inputs are random, sorted, reversed and duplicate-heavy records. Each full result and top-k prefix is checked against the same reference order.

| Records | Input | Method | k | Mean ms |
| ---: | --- | --- | ---: | ---: |
| 50 | random | merge | - | 0.2655 |
| 50 | random | quick | - | 0.1637 |
| 50 | random | heap | - | 0.2960 |
| 50 | random | top_k | 5 | 0.0580 |
| 50 | random | top_k | 49 | 0.1339 |
| 50 | sorted | merge | - | 0.1377 |
| 50 | sorted | quick | - | 0.0991 |
| 50 | sorted | heap | - | 0.2911 |
| 50 | sorted | top_k | 5 | 0.0457 |
| 50 | sorted | top_k | 49 | 0.1504 |
| 50 | reverse | merge | - | 0.1538 |
| 50 | reverse | quick | - | 0.1019 |
| 50 | reverse | heap | - | 0.4620 |
| 50 | reverse | top_k | 5 | 0.1451 |
| 50 | reverse | top_k | 49 | 0.1954 |
| 50 | duplicates | merge | - | 0.2028 |
| 50 | duplicates | quick | - | 0.1773 |
| 50 | duplicates | heap | - | 0.2325 |
| 50 | duplicates | top_k | 5 | 0.0529 |
| 50 | duplicates | top_k | 49 | 0.1327 |
| 200 | random | merge | - | 1.7959 |
| 200 | random | quick | - | 0.7614 |
| 200 | random | heap | - | 1.7856 |
| 200 | random | top_k | 5 | 0.1877 |
| 200 | random | top_k | 199 | 1.1305 |
| 200 | sorted | merge | - | 0.7185 |
| 200 | sorted | quick | - | 0.5433 |
| 200 | sorted | heap | - | 2.1007 |
| 200 | sorted | top_k | 5 | 0.1378 |
| 200 | sorted | top_k | 199 | 0.7650 |
| 200 | reverse | merge | - | 0.7993 |
| 200 | reverse | quick | - | 0.5646 |
| 200 | reverse | heap | - | 1.8472 |
| 200 | reverse | top_k | 5 | 0.1981 |
| 200 | reverse | top_k | 199 | 0.7636 |
| 200 | duplicates | merge | - | 1.4229 |
| 200 | duplicates | quick | - | 2.0177 |
| 200 | duplicates | heap | - | 1.3907 |
| 200 | duplicates | top_k | 5 | 0.4676 |
| 200 | duplicates | top_k | 199 | 1.0885 |
| 500 | random | merge | - | 3.6522 |
| 500 | random | quick | - | 3.6760 |
| 500 | random | heap | - | 6.0924 |
| 500 | random | top_k | 5 | 0.5331 |
| 500 | random | top_k | 499 | 2.6301 |
| 500 | sorted | merge | - | 2.1854 |
| 500 | sorted | quick | - | 1.9621 |
| 500 | sorted | heap | - | 5.7586 |
| 500 | sorted | top_k | 5 | 0.3745 |
| 500 | sorted | top_k | 499 | 2.9931 |
| 500 | reverse | merge | - | 2.3866 |
| 500 | reverse | quick | - | 2.2885 |
| 500 | reverse | heap | - | 4.8228 |
| 500 | reverse | top_k | 5 | 0.5223 |
| 500 | reverse | top_k | 499 | 2.5275 |
| 500 | duplicates | merge | - | 3.1151 |
| 500 | duplicates | quick | - | 9.5047 |
| 500 | duplicates | heap | - | 5.2749 |
| 500 | duplicates | top_k | 5 | 0.4573 |
| 500 | duplicates | top_k | 499 | 5.4194 |

Top-k uses bottom-up heap construction followed by k extractions: O(n + k log n), with O(n) storage. Full sorting and retrieval have different output sizes, so comparisons should consider k relative to n. These measurements include comparator and heap setup; comparison counters are not currently instrumented.
