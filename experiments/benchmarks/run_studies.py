"""Run the assignment studies using the actual game algorithms.

Run from the repository root: python experiments/benchmarks/run_studies.py
Timing includes each algorithm's own setup and trace construction, but excludes
input generation, validation, file I/O, rendering and artificial delays.
"""

import json
from importlib.metadata import PackageNotFoundError, version
import platform
import random
import statistics
import sys
from itertools import combinations
from pathlib import Path
from time import perf_counter

from smart_racing.algorithms.graph.traversal import bfs, dfs, has_cycle, weak_components
from smart_racing.algorithms.optimization.resources import Pickup, greedy, knapsack
from smart_racing.algorithms.routing.shortest import shortest_path
from smart_racing.algorithms.sorting.rankings import heap_sort, merge_sort, quick_sort, top_k
from smart_racing.core.graph import Edge, Graph, Vertex
from smart_racing.championship.standings import ChampionshipEntry, ranking_key
from smart_racing.events.queue import Event, EventQueue


SEED = 20261205
REPEATS = 5
ROOT = Path(__file__).resolve().parents[2]


def measure(operation):
    operation()  # warm-up
    samples = []
    for _ in range(REPEATS):
        start = perf_counter()
        operation()
        samples.append((perf_counter() - start) * 1000)
    return {"samples_ms": samples, "mean_ms": statistics.mean(samples),
            "median_ms": statistics.median(samples)}


def measure_prepared(prepare, operation):
    operation(prepare())
    samples = []
    for _ in range(REPEATS):
        prepared = prepare()
        start = perf_counter()
        operation(prepared)
        samples.append((perf_counter() - start) * 1000)
    return {"samples_ms": samples, "mean_ms": statistics.mean(samples),
            "median_ms": statistics.median(samples)}


def graph_for(size, dense, seed):
    rng = random.Random(seed)
    graph = Graph()
    for vertex in range(size):
        graph.add_vertex(Vertex(vertex, rng.random() * 100, rng.random() * 100))
    pairs = {(i, i + 1) for i in range(size - 1)}
    probability = .12 if dense else 2 / size
    for a in range(size):
        for b in range(a + 1, size):
            if rng.random() < probability:
                pairs.add((a, b))
    for edge_id, (a, b) in enumerate(sorted(pairs)):
        length = rng.uniform(1, 25)
        graph.add_edge(Edge(edge_id, a, b, length, length / 5, length / 10))
    return graph


def traversal_study():
    rows = []
    for size in (20, 60, 120):
        for dense in (False, True):
            graph = graph_for(size, dense, SEED + size + int(dense))
            components = weak_components(graph)
            cycle = has_cycle(graph)
            assert len(components) == 1
            assert cycle == (len(graph.edges) >= len(graph.vertices))
            for name, algorithm in (("bfs", bfs), ("dfs", dfs)):
                result = algorithm(graph, 0)
                assert len(result.order) == size
                rows.append({"vertices": size, "edges": len(graph.edges), "dense": dense,
                             "algorithm": name, "visited": len(result.order),
                             "examined_edges": result.examined_edges, "components": len(components),
                             "cycle": cycle,
                             "timing": measure(lambda: algorithm(graph, 0))})
    return rows


def routing_study():
    rows = []
    for size in (20, 60, 120):
        graph = graph_for(size, False, SEED + size)
        first = shortest_path(graph, 0, size - 1)
        second = shortest_path(graph, 0, size - 1, algorithm="astar")
        assert abs(first.cost - second.cost) < 1e-8
        for name, result in (("dijkstra", first), ("astar", second)):
            rows.append({"vertices": size, "edges": len(graph.edges), "algorithm": name,
                         "cost": result.cost, "expanded": result.expanded, "relaxed": result.relaxed,
                         "heap_operations": result.heap_operations,
                         "timing": measure(lambda: shortest_path(graph, 0, size - 1, algorithm=name))})
    return rows


def resource_study():
    rows = []
    rng = random.Random(SEED)
    examples = [([Pickup(1, 6, 30), Pickup(2, 5, 24), Pickup(3, 5, 24)], 10),
                ([Pickup(1, 4, 12), Pickup(2, 3, 8), Pickup(3, 3, 8)], 6),
                ([Pickup(1, 5, 20), Pickup(2, 4, 15), Pickup(3, 4, 15)], 8)]
    for items, budget in examples:
        assert greedy(items, budget).benefit < knapsack(items, budget).benefit
        best = max(sum(item.benefit for item in subset) for count in range(len(items) + 1)
                   for subset in combinations(items, count) if sum(item.cost for item in subset) <= budget)
        assert knapsack(items, budget).benefit == best
    for size, budget in ((10, 30), (30, 60), (60, 100)):
        items = [Pickup(i, rng.randint(1, 12), rng.randint(1, 30)) for i in range(size)]
        for name, algorithm in (("dp", knapsack), ("greedy", greedy)):
            result = algorithm(items, budget)
            assert result.cost <= budget
            rows.append({"items": size, "budget": budget, "algorithm": name,
                         "benefit": result.benefit, "selected": [i.id for i in result.items],
                         "states": result.states, "timing": measure(lambda: algorithm(items, budget))})
    return {"cases": [{"items": [{"id": i.id, "cost": i.cost, "benefit": i.benefit} for i in items],
                       "budget": budget, "dp": knapsack(items, budget).benefit,
                       "greedy": greedy(items, budget).benefit} for items, budget in examples], "rows": rows}


def queue_study():
    rows = []
    for size in (50, 250, 1000):
        rng = random.Random(SEED + size)
        values = [(rng.randrange(12), rng.randrange(1, 7)) for _ in range(size)]

        def prepare():
            queue = EventQueue()
            for index, (time, priority) in enumerate(values):
                queue.schedule(Event(index, time, priority, "block", 0))
            for index in range(0, size, 11):
                queue.cancel(index)
            return queue

        queue = prepare()
        events = list(queue.due(20))
        operations = queue.heap.operations
        expected = sorted((time, priority, index) for index, (time, priority) in enumerate(values) if index % 11)
        assert [(event.time, event.priority, event.id) for event in events] == expected
        rows.append({"events": size, "cancelled": size - len(events), "heap_operations": operations,
                     "insert_and_cancel_timing": measure(prepare),
                     "extraction_timing": measure_prepared(prepare, lambda item: list(item.due(20)))})
    return rows


def sorting_study():
    rows = []
    rng = random.Random(SEED)
    for size in (50, 200, 500):
        random_values = [ChampionshipEntry(i, f"Racer {i}", rng.randrange(size), rng.randrange(4),
                                           rng.randrange(size), float(rng.randrange(100))) for i in range(size)]
        duplicate_values = [ChampionshipEntry(i, f"Racer {i}", i % 5, 0, 0, 10.0) for i in range(size)]
        for kind, values in (("random", random_values), ("sorted", sorted(random_values, key=ranking_key)),
                             ("reverse", sorted(random_values, key=ranking_key, reverse=True)),
                             ("duplicates", duplicate_values)):
            expected = sorted(values, key=ranking_key)
            for name, method in (("merge", merge_sort), ("quick", quick_sort), ("heap", heap_sort)):
                assert method(values, key=ranking_key) == expected
                rows.append({"size": size, "input": kind, "algorithm": name,
                             "timing": measure(lambda: method(values, key=ranking_key))})
            for k in (5, size - 1):
                assert top_k(values, k, key=ranking_key) == expected[:k]
                rows.append({"size": size, "input": kind, "algorithm": "top_k", "k": k,
                             "timing": measure(lambda: top_k(values, k, key=ranking_key))})
    return rows


def write_analysis(output):
    environment = output["environment"]
    lines = ["# Experimental studies - measured prototype results", "",
             "These are actual measurements from the current implementation, not projected results. "
             "Rerun `python experiments/benchmarks/run_studies.py` from the repository root to regenerate "
             "this file and `studies.json`.", "",
             f"Environment: {environment['platform']}; {environment['processor']}; Python {environment['python']}. "
             f"Dependency versions: {environment['dependencies']}. "
             f"Seed: {SEED}. Each timing has one warm-up and {REPEATS} measured repetitions; values "
             "below are means in milliseconds. Raw samples and medians are in `studies.json`. "
             + environment["timing"] + ".", "",
             "## 1. BFS and DFS", "",
             "Objective: compare traversal time and work as graph size and density vary. "
             "Inputs are seeded connected undirected graphs with a chain and extra sparse or denser roads. "
             "The script checks reachability, weak components and cycle presence outside timed regions.", "",
             "| Vertices | Edges | Density | Algorithm | Visited | Examined roads | Mean ms |",
             "| ---: | ---: | --- | --- | ---: | ---: | ---: |"]
    for row in output["traversal"]:
        lines.append(f"| {row['vertices']} | {row['edges']} | {'denser' if row['dense'] else 'sparse'} | "
                     f"{row['algorithm']} | {row['visited']} | {row['examined_edges']} | {row['timing']['mean_ms']:.4f} |")
    lines += ["", "Both traversals visit all vertices in these connected inputs. Examined road counts "
              "depend on adjacency entries, including both directions of undirected roads. "
              "The small sizes, trace collection and machine noise limit timing conclusions; theoretical "
              "time remains O(V+E).", "", "## 2. Dijkstra and A*", "",
              "Objective: compare optimal routing on identical seeded sparse graphs with non-negative "
              "normalized costs. Coordinates are randomly generated and road costs need not equal "
              "geometric length. The heuristic uses the minimum edge cost per geometric unit. "
              "The script checks equal final costs outside timed regions.", "",
              "| Vertices | Edges | Algorithm | Cost | Expanded | Relaxed | Heap operations | Mean ms |",
              "| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in output["routing"]:
        lines.append(f"| {row['vertices']} | {row['edges']} | {row['algorithm']} | {row['cost']:.4f} | "
                     f"{row['expanded']} | {row['relaxed']} | {row['heap_operations']} | {row['timing']['mean_ms']:.4f} |")
    lines += ["", "Equal optimal costs are verified for each paired input. The heuristic may be weak, "
              "and its setup is timed, so A* need not be faster or expand fewer vertices in every case. "
              "These instances alone do not establish general performance.", "", "## 3. Dynamic programming and greedy", "",
              "Objective: compare 0/1 pickup benefit and runtime as item count and budget vary. "
              "Seeded item costs and benefits are generated before timing. Three small counterexamples "
              "are separately checked against exhaustive search.", "",
              "| Items | Budget | Method | Benefit | DP states | Mean ms |",
              "| ---: | ---: | --- | ---: | ---: | ---: |"]
    for row in output["resources"]["rows"]:
        lines.append(f"| {row['items']} | {row['budget']} | {row['algorithm']} | {row['benefit']} | "
                     f"{row['states']} | {row['timing']['mean_ms']:.4f} |")
    lines += ["", "Counterexamples (budget, DP benefit, greedy benefit): " + "; ".join(
        f"({case['budget']}, {case['dp']}, {case['greedy']})" for case in output["resources"]["cases"]) + ". "
        "The selected IDs and input cases are saved in the raw JSON. DP is pseudo-polynomial in "
        "budget; greedy is feasible but need not be optimal. These small instances do not establish "
        "the performance of larger multi-resource planners.", "", "## 4. Event priority queue", "",
        "Objective: measure insertion/cancellation and extraction separately for seeded event queues. "
        "Inputs contain tied timestamps and priorities; every eleventh event is lazily cancelled. "
        "The result order is checked against time, priority and insertion sequence. Independent "
        "effect expiration is exercised by the automated race tests.", "",
        "| Events | Cancelled | Heap operations | Insert + cancel ms | Extraction ms |",
        "| ---: | ---: | ---: | ---: | ---: |"]
    for row in output["events"]:
        lines.append(f"| {row['events']} | {row['cancelled']} | {row['heap_operations']} | "
                     f"{row['insert_and_cancel_timing']['mean_ms']:.4f} | {row['extraction_timing']['mean_ms']:.4f} |")
    lines += ["", "Extraction timing excludes preparing the queue; insertion includes queue creation. "
              "Lazy cancellation keeps entries in memory until extraction, so the benchmark reports "
              "operations for cancelled entries as well.", "", "## 5. Sorting and top-k", "",
              "Objective: compare the three manual sorts and heap top-k using the actual championship "
              "total comparator. Inputs are random, sorted, reversed and duplicate-heavy records. "
              "Each full result and top-k prefix is checked against the same reference order.", "",
              "| Records | Input | Method | k | Mean ms |", "| ---: | --- | --- | ---: | ---: |"]
    for row in output["sorting"]:
        lines.append(f"| {row['size']} | {row['input']} | {row['algorithm']} | {row.get('k', '-')} | "
                     f"{row['timing']['mean_ms']:.4f} |")
    lines += ["", "Top-k uses bottom-up heap construction followed by k extractions: O(n + k log n), "
              "with O(n) storage. Full sorting and retrieval have different output sizes, so comparisons "
              "should consider k relative to n. These measurements include comparator and heap setup; "
              "comparison counters are not currently instrumented.", ""]
    (ROOT / "experiments" / "results" / "analysis.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    dependencies = {}
    for package in ("smart-racing-championship", "pygame", "pytest", "matplotlib"):
        try:
            dependencies[package] = version(package)
        except PackageNotFoundError:
            dependencies[package] = "not installed"
    output = {"environment": {"python": sys.version, "platform": platform.platform(),
                              "processor": platform.processor(), "seed": SEED, "repeats": REPEATS,
                              "dependencies": dependencies,
                              "timing": "perf_counter; milliseconds; one warm-up; algorithm initialization included except prepared event extraction; input generation, correctness checks, I/O and rendering excluded"},
              "traversal": traversal_study(), "routing": routing_study(),
              "resources": resource_study(), "events": queue_study(), "sorting": sorting_study()}
    destination = ROOT / "experiments" / "results" / "studies.json"
    destination.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    write_analysis(output)
    print(f"Wrote measured results to {destination}")


if __name__ == "__main__":
    main()
