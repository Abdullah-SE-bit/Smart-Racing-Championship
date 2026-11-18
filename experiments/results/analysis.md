# Experimental studies - measured prototype results

These are actual measurements from the current implementation, not projected results. Rerun `python experiments/benchmarks/run_studies.py` from the repository root to regenerate this file and `studies.json`.

Environment: Windows-11-10.0.26300-SP0; Intel64 Family 6 Model 142 Stepping 10, GenuineIntel; Python 3.12.16 (main, Oct 26 2026, 14:10:56) [MSC v.1944 64 bit (AMD64)]. Dependency versions: {'smart-racing-championship': '0.0.0', 'pygame': '2.6.1', 'pytest': '9.2.0', 'matplotlib': '3.11.2'}. Seed: 20261205. Each timing has one warm-up and 5 measured repetitions; values below are means in milliseconds. Raw samples and medians are in `studies.json`. perf_counter; milliseconds; one warm-up; algorithm initialization included except prepared event extraction; input generation, correctness checks, I/O and rendering excluded.

## 1. BFS and DFS

Objective: compare traversal time and work as graph size and density vary. Inputs are seeded connected undirected graphs with a chain and extra sparse or denser roads. The script checks reachability, BFS minimum-edge paths against an independent repeated-relaxation reference, weak components and cycle presence outside timed regions.

| Vertices | Edges | Density | Algorithm | Visited | Examined roads | Mean ms |
| ---: | ---: | --- | --- | ---: | ---: | ---: |
| 20 | 31 | sparse | bfs | 20 | 62 | 0.0257 |
| 20 | 31 | sparse | dfs | 20 | 62 | 0.0345 |
| 20 | 34 | denser | bfs | 20 | 68 | 0.0263 |
| 20 | 34 | denser | dfs | 20 | 68 | 0.0361 |
| 60 | 116 | sparse | bfs | 60 | 232 | 0.0878 |
| 60 | 116 | sparse | dfs | 60 | 232 | 0.1136 |
| 60 | 249 | denser | bfs | 60 | 498 | 0.1417 |
| 60 | 249 | denser | dfs | 60 | 498 | 0.1917 |
| 120 | 240 | sparse | bfs | 120 | 480 | 0.1970 |
| 120 | 240 | sparse | dfs | 120 | 480 | 0.2471 |
| 120 | 953 | denser | bfs | 120 | 1906 | 0.4975 |
| 120 | 953 | denser | dfs | 120 | 1906 | 0.6766 |

Both traversals visit all vertices in these connected inputs. Examined road counts depend on adjacency entries, including both directions of undirected roads. The small sizes, trace collection and machine noise limit timing conclusions; theoretical time remains O(V+E).

## 2. Dijkstra and A*

Objective: compare optimal routing on identical seeded sparse graphs with non-negative normalized costs. Coordinates are randomly generated and road costs need not equal geometric length. The heuristic uses the minimum edge cost per geometric unit. The script checks equal final costs outside timed regions. Routing heap operations count insertions, priority decreases and extractions.

| Vertices | Edges | Algorithm | Cost | Expanded | Relaxed | Heap operations | Mean ms |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 20 | 31 | dijkstra | 1.5391 | 14 | 41 | 33 | 0.0892 |
| 20 | 31 | astar | 1.5391 | 14 | 41 | 33 | 0.1770 |
| 60 | 116 | dijkstra | 1.0050 | 24 | 104 | 77 | 0.2232 |
| 60 | 116 | astar | 1.0050 | 23 | 97 | 75 | 0.3312 |
| 120 | 240 | dijkstra | 1.2432 | 67 | 279 | 205 | 0.6297 |
| 120 | 240 | astar | 1.2432 | 64 | 268 | 199 | 1.0781 |

A* expanded fewer vertices in 2 inputs, equal numbers in 1, and more in 0. Unobserved cases are not evidence that they cannot occur. Equal optimal costs are verified for each paired input. The heuristic may be weak, and its setup is timed, so A* need not be faster or expand fewer vertices in every case. These instances alone do not establish general performance.

## 3. Dynamic programming and greedy

Objective: compare 0/1 pickup benefit and runtime as item count and budget vary. All cases, including the assignment example and two team counterexamples, are timed. Each counterexample is checked against exhaustive search before timing.

| Items | Budget | Method | Benefit | DP states | Mean ms |
| ---: | ---: | --- | ---: | ---: | ---: |
| 3 | 10 | dp | 48 | 33 | 0.0098 |
| 3 | 10 | greedy | 30 | 0 | 0.0113 |
| 3 | 6 | dp | 16 | 21 | 0.0076 |
| 3 | 6 | greedy | 12 | 0 | 0.0109 |
| 3 | 8 | dp | 30 | 27 | 0.0086 |
| 3 | 8 | greedy | 20 | 0 | 0.0108 |
| 10 | 30 | dp | 109 | 310 | 0.0783 |
| 10 | 30 | greedy | 109 | 0 | 0.0903 |
| 30 | 60 | dp | 252 | 1830 | 0.4659 |
| 30 | 60 | greedy | 252 | 0 | 0.4789 |
| 60 | 100 | dp | 551 | 6060 | 1.9174 |
| 60 | 100 | greedy | 550 | 0 | 1.5329 |

Counterexamples (budget, DP benefit, greedy benefit): (10, 48, 30); (6, 16, 12); (8, 30, 20). The selected IDs and input cases are saved in the raw JSON. DP is pseudo-polynomial in budget; greedy is feasible but need not be optimal. These small instances do not establish the performance of larger multi-resource planners.

## 4. Event priority queue

Objective: measure insertion and extraction separately for seeded queues. Timestamps and priorities include ties. Before extraction, every eleventh event is lazily cancelled. The reference order uses trigger time, priority and insertion sequence. In a separate race check, two closures start at t=1. The road stays blocked after one expires at t=3 and opens at t=6. The raw results record the surviving effects at each time.

| Events | Cancelled | Heap operations | Insertion ms | Extraction ms |
| ---: | ---: | ---: | ---: | ---: |
| 50 | 5 | 100 | 0.1886 | 0.0922 |
| 250 | 23 | 500 | 0.9488 | 0.8288 |
| 1000 | 91 | 2000 | 4.5000 | 3.9191 |

Extraction timing excludes preparing the queue; insertion includes queue creation. Lazy cancellation keeps entries in memory until extraction, so the benchmark reports operations for cancelled entries as well.

## 5. Sorting and top-k

Objective: compare the three manual sorts and heap top-k using the actual championship total comparator. Inputs are random, sorted, reversed and duplicate-heavy records. Each full result and top-k prefix is checked against the same reference order.

| Records | Input | Method | k | Mean ms |
| ---: | --- | --- | ---: | ---: |
| 50 | random | merge | - | 0.2419 |
| 50 | random | quick | - | 0.2073 |
| 50 | random | heap | - | 0.1979 |
| 50 | random | top_k | 5 | 0.0604 |
| 50 | random | top_k | 49 | 0.1963 |
| 50 | sorted | merge | - | 0.1138 |
| 50 | sorted | quick | - | 0.0822 |
| 50 | sorted | heap | - | 0.2128 |
| 50 | sorted | top_k | 5 | 0.0305 |
| 50 | sorted | top_k | 49 | 0.2202 |
| 50 | reverse | merge | - | 0.1225 |
| 50 | reverse | quick | - | 0.0893 |
| 50 | reverse | heap | - | 0.1829 |
| 50 | reverse | top_k | 5 | 0.1229 |
| 50 | reverse | top_k | 49 | 0.4813 |
| 50 | duplicates | merge | - | 0.2160 |
| 50 | duplicates | quick | - | 0.1165 |
| 50 | duplicates | heap | - | 0.1894 |
| 50 | duplicates | top_k | 5 | 0.0488 |
| 50 | duplicates | top_k | 49 | 0.2018 |
| 200 | random | merge | - | 0.8279 |
| 200 | random | quick | - | 0.7464 |
| 200 | random | heap | - | 1.1840 |
| 200 | random | top_k | 5 | 0.1340 |
| 200 | random | top_k | 199 | 1.3931 |
| 200 | sorted | merge | - | 0.5628 |
| 200 | sorted | quick | - | 0.4374 |
| 200 | sorted | heap | - | 1.3522 |
| 200 | sorted | top_k | 5 | 0.0940 |
| 200 | sorted | top_k | 199 | 1.2826 |
| 200 | reverse | merge | - | 0.7815 |
| 200 | reverse | quick | - | 0.4414 |
| 200 | reverse | heap | - | 1.0876 |
| 200 | reverse | top_k | 5 | 0.8235 |
| 200 | reverse | top_k | 199 | 1.0217 |
| 200 | duplicates | merge | - | 0.7647 |
| 200 | duplicates | quick | - | 1.2093 |
| 200 | duplicates | heap | - | 1.1072 |
| 200 | duplicates | top_k | 5 | 0.1624 |
| 200 | duplicates | top_k | 199 | 1.0874 |
| 500 | random | merge | - | 2.8649 |
| 500 | random | quick | - | 1.8383 |
| 500 | random | heap | - | 4.0249 |
| 500 | random | top_k | 5 | 0.3066 |
| 500 | random | top_k | 499 | 4.1660 |
| 500 | sorted | merge | - | 2.0886 |
| 500 | sorted | quick | - | 1.2904 |
| 500 | sorted | heap | - | 3.9842 |
| 500 | sorted | top_k | 5 | 0.2485 |
| 500 | sorted | top_k | 499 | 4.1214 |
| 500 | reverse | merge | - | 2.0364 |
| 500 | reverse | quick | - | 1.2841 |
| 500 | reverse | heap | - | 3.8440 |
| 500 | reverse | top_k | 5 | 1.6055 |
| 500 | reverse | top_k | 499 | 3.3314 |
| 500 | duplicates | merge | - | 2.3953 |
| 500 | duplicates | quick | - | 7.3224 |
| 500 | duplicates | heap | - | 3.6784 |
| 500 | duplicates | top_k | 5 | 0.2334 |
| 500 | duplicates | top_k | 499 | 3.6843 |

For 500 random records, the bounded heap averaged 0.3066 ms for k=5 and 4.1660 ms for k=499. Merge Sort ranked the entire field in 2.8649 ms. The heap retains at most k entries and runs in O(n log(k+1)) time with O(k) storage. As k approaches n, its memory and extraction costs approach those of a full ranking. These timings include comparator and heap setup and depend on the input order and machine.
