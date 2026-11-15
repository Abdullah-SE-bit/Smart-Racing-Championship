# Experimental studies - measured prototype results

These are actual measurements from the current implementation, not projected results. Rerun `python experiments/benchmarks/run_studies.py` from the repository root to regenerate this file and `studies.json`.

Environment: Windows-11-10.0.26300-SP0; Intel64 Family 6 Model 142 Stepping 10, GenuineIntel; Python 3.12.16 (main, Oct 26 2026, 14:10:56) [MSC v.1944 64 bit (AMD64)]. Dependency versions: {'smart-racing-championship': '0.0.0', 'pygame': '2.6.1', 'pytest': '9.2.0', 'matplotlib': '3.11.2'}. Seed: 20261205. Each timing has one warm-up and 5 measured repetitions; values below are means in milliseconds. Raw samples and medians are in `studies.json`. perf_counter; milliseconds; one warm-up; algorithm initialization included except prepared event extraction; input generation, correctness checks, I/O and rendering excluded.

## 1. BFS and DFS

Objective: compare traversal time and work as graph size and density vary. Inputs are seeded connected undirected graphs with a chain and extra sparse or denser roads. The script checks reachability, weak components and cycle presence outside timed regions.

| Vertices | Edges | Density | Algorithm | Visited | Examined roads | Mean ms |
| ---: | ---: | --- | --- | ---: | ---: | ---: |
| 20 | 31 | sparse | bfs | 20 | 62 | 0.1380 |
| 20 | 31 | sparse | dfs | 20 | 62 | 0.2093 |
| 20 | 34 | denser | bfs | 20 | 68 | 0.1393 |
| 20 | 34 | denser | dfs | 20 | 68 | 0.2091 |
| 60 | 116 | sparse | bfs | 60 | 232 | 0.4593 |
| 60 | 116 | sparse | dfs | 60 | 232 | 0.6701 |
| 60 | 249 | denser | bfs | 60 | 498 | 0.8718 |
| 60 | 249 | denser | dfs | 60 | 498 | 0.9623 |
| 120 | 240 | sparse | bfs | 120 | 480 | 1.1353 |
| 120 | 240 | sparse | dfs | 120 | 480 | 1.4332 |
| 120 | 953 | denser | bfs | 120 | 1906 | 5.8917 |
| 120 | 953 | denser | dfs | 120 | 1906 | 5.9130 |

Both traversals visit all vertices in these connected inputs. Examined road counts depend on adjacency entries, including both directions of undirected roads. The small sizes, trace collection and machine noise limit timing conclusions; theoretical time remains O(V+E).

## 2. Dijkstra and A*

Objective: compare optimal routing on identical seeded sparse graphs with non-negative normalized costs. Coordinates are randomly generated and road costs need not equal geometric length. The heuristic uses the minimum edge cost per geometric unit. The script checks equal final costs outside timed regions.

| Vertices | Edges | Algorithm | Cost | Expanded | Relaxed | Heap operations | Mean ms |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 20 | 31 | dijkstra | 1.5391 | 14 | 41 | 33 | 0.4372 |
| 20 | 31 | astar | 1.5391 | 14 | 41 | 33 | 0.4366 |
| 60 | 116 | dijkstra | 1.0050 | 24 | 104 | 77 | 2.2440 |
| 60 | 116 | astar | 1.0050 | 23 | 97 | 75 | 1.3898 |
| 120 | 240 | dijkstra | 1.2432 | 67 | 279 | 208 | 4.6157 |
| 120 | 240 | astar | 1.2432 | 64 | 268 | 201 | 4.1833 |

Equal optimal costs are verified for each paired input. The heuristic may be weak, and its setup is timed, so A* need not be faster or expand fewer vertices in every case. These instances alone do not establish general performance.

## 3. Dynamic programming and greedy

Objective: compare 0/1 pickup benefit and runtime as item count and budget vary. Seeded item costs and benefits are generated before timing. Three small counterexamples are separately checked against exhaustive search.

| Items | Budget | Method | Benefit | DP states | Mean ms |
| ---: | ---: | --- | ---: | ---: | ---: |
| 10 | 30 | dp | 109 | 310 | 0.4061 |
| 10 | 30 | greedy | 109 | 0 | 0.5530 |
| 30 | 60 | dp | 252 | 1830 | 2.5749 |
| 30 | 60 | greedy | 252 | 0 | 3.5432 |
| 60 | 100 | dp | 551 | 6060 | 7.7374 |
| 60 | 100 | greedy | 550 | 0 | 7.6471 |

Counterexamples (budget, DP benefit, greedy benefit): (10, 48, 30); (6, 16, 12); (8, 30, 20). The selected IDs and input cases are saved in the raw JSON. DP is pseudo-polynomial in budget; greedy is feasible but need not be optimal. These small instances do not establish the performance of larger multi-resource planners.

## 4. Event priority queue

Objective: measure insertion/cancellation and extraction separately for seeded event queues. Inputs contain tied timestamps and priorities; every eleventh event is lazily cancelled. The result order is checked against time, priority and insertion sequence. Independent effect expiration is exercised by the automated race tests.

| Events | Cancelled | Heap operations | Insert + cancel ms | Extraction ms |
| ---: | ---: | ---: | ---: | ---: |
| 50 | 5 | 100 | 2.0713 | 0.7004 |
| 250 | 23 | 500 | 5.9378 | 3.8586 |
| 1000 | 91 | 2000 | 26.6151 | 15.9199 |

Extraction timing excludes preparing the queue; insertion includes queue creation. Lazy cancellation keeps entries in memory until extraction, so the benchmark reports operations for cancelled entries as well.

## 5. Sorting and top-k

Objective: compare the three manual sorts and heap top-k using the actual championship total comparator. Inputs are random, sorted, reversed and duplicate-heavy records. Each full result and top-k prefix is checked against the same reference order.

| Records | Input | Method | k | Mean ms |
| ---: | --- | --- | ---: | ---: |
| 50 | random | merge | - | 0.6828 |
| 50 | random | quick | - | 0.4143 |
| 50 | random | heap | - | 0.9939 |
| 50 | random | top_k | 5 | 0.2251 |
| 50 | random | top_k | 49 | 0.6406 |
| 50 | sorted | merge | - | 0.5766 |
| 50 | sorted | quick | - | 0.3942 |
| 50 | sorted | heap | - | 0.7410 |
| 50 | sorted | top_k | 5 | 0.1248 |
| 50 | sorted | top_k | 49 | 0.3729 |
| 50 | reverse | merge | - | 0.4225 |
| 50 | reverse | quick | - | 0.3939 |
| 50 | reverse | heap | - | 0.6690 |
| 50 | reverse | top_k | 5 | 0.2224 |
| 50 | reverse | top_k | 49 | 0.2748 |
| 50 | duplicates | merge | - | 0.5291 |
| 50 | duplicates | quick | - | 0.6004 |
| 50 | duplicates | heap | - | 0.9064 |
| 50 | duplicates | top_k | 5 | 0.1657 |
| 50 | duplicates | top_k | 49 | 0.5755 |
| 200 | random | merge | - | 2.9962 |
| 200 | random | quick | - | 1.2929 |
| 200 | random | heap | - | 4.0874 |
| 200 | random | top_k | 5 | 0.8997 |
| 200 | random | top_k | 199 | 1.9895 |
| 200 | sorted | merge | - | 1.9748 |
| 200 | sorted | quick | - | 1.3371 |
| 200 | sorted | heap | - | 3.3687 |
| 200 | sorted | top_k | 5 | 0.2348 |
| 200 | sorted | top_k | 199 | 1.9917 |
| 200 | reverse | merge | - | 2.5203 |
| 200 | reverse | quick | - | 2.0875 |
| 200 | reverse | heap | - | 4.1091 |
| 200 | reverse | top_k | 5 | 0.5590 |
| 200 | reverse | top_k | 199 | 3.1179 |
| 200 | duplicates | merge | - | 3.0471 |
| 200 | duplicates | quick | - | 4.8389 |
| 200 | duplicates | heap | - | 3.4124 |
| 200 | duplicates | top_k | 5 | 0.7690 |
| 200 | duplicates | top_k | 199 | 2.9626 |
| 500 | random | merge | - | 9.3865 |
| 500 | random | quick | - | 7.7934 |
| 500 | random | heap | - | 39.6517 |
| 500 | random | top_k | 5 | 1.6816 |
| 500 | random | top_k | 499 | 7.6745 |
| 500 | sorted | merge | - | 7.5418 |
| 500 | sorted | quick | - | 5.0038 |
| 500 | sorted | heap | - | 18.3631 |
| 500 | sorted | top_k | 5 | 1.5490 |
| 500 | sorted | top_k | 499 | 15.4097 |
| 500 | reverse | merge | - | 22.1307 |
| 500 | reverse | quick | - | 9.1755 |
| 500 | reverse | heap | - | 21.4235 |
| 500 | reverse | top_k | 5 | 3.4492 |
| 500 | reverse | top_k | 499 | 22.3137 |
| 500 | duplicates | merge | - | 20.1625 |
| 500 | duplicates | quick | - | 41.2752 |
| 500 | duplicates | heap | - | 23.5805 |
| 500 | duplicates | top_k | 5 | 4.6411 |
| 500 | duplicates | top_k | 499 | 12.3933 |

Top-k uses bottom-up heap construction followed by k extractions: O(n + k log n), with O(n) storage. Full sorting and retrieval have different output sizes, so comparisons should consider k relative to n. These measurements include comparator and heap setup; comparison counters are not currently instrumented.
