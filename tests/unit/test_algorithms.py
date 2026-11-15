from itertools import combinations
from math import inf
from random import Random

import pytest

from smart_racing.algorithms.generation.mst import kruskal
from smart_racing.algorithms.graph.traversal import bfs, bounded_simple_paths, dead_ends, dfs, has_cycle, simple_paths, weak_components
from smart_racing.algorithms.optimization.resources import Pickup, greedy, knapsack, refuel_plan
from smart_racing.algorithms.routing.shortest import checkpoint_route, shortest_path
from smart_racing.algorithms.sorting.rankings import heap_sort, merge_sort, quick_sort, top_k
from smart_racing.algorithms.structures.heap import MinHeap
from smart_racing.core.graph import CostProfile, Edge, Graph, Vertex
from smart_racing.resources.planner import route_refuelling
from smart_racing.championship.standings import ChampionshipEntry, ranking_key


def sample_graph():
    graph = Graph()
    for index, (x, y) in enumerate([(0, 0), (1, 0), (2, 0), (1, 1), (8, 8)]):
        graph.add_vertex(Vertex(index, x, y))
    for edge in [Edge(0, 0, 1, 1, 1, 1), Edge(1, 1, 2, 1, 1, 1),
                 Edge(2, 0, 2, 5, 5, 5), Edge(3, 1, 3, 1, 1, 1, directed=True)]:
        graph.add_edge(edge)
    return graph


def test_traversals_reachability_and_simple_paths():
    graph = sample_graph()
    assert bfs(graph, 0).path_to(2) == [0, 2]
    assert bfs(graph, 0).path_to(0) == [0]
    assert bfs(graph, 0).path_to(4) == []
    assert dfs(graph, 3).order == [3]
    assert len(simple_paths(graph, 0, 2, limit=1)) == 1
    assert simple_paths(graph, 0, 2, limit=0) == []
    assert has_cycle(graph)
    assert len(weak_components(graph)) == 2
    assert 3 in dead_ends(graph, 0)
    graph.edges[2].status = "blocked"
    assert bfs(graph, 0).path_to(2) == [0, 1, 2]


def test_bounded_alternative_paths_report_limits_and_avoid_parallel_duplicates():
    graph = sample_graph()
    graph.add_edge(Edge(9, 0, 1, 2, 2, 2))
    paths, truncated = bounded_simple_paths(graph, 0, 2, limit=10)
    assert paths == [[0, 1, 2], [0, 2]]
    assert not truncated
    paths, truncated = bounded_simple_paths(graph, 0, 2, limit=1)
    assert len(paths) == 1 and truncated
    paths, truncated = bounded_simple_paths(graph, 0, 4, max_states=2)
    assert paths == [] and truncated
    paths, truncated = bounded_simple_paths(graph, 0, 2, max_length=2)
    assert paths == [[0, 2]] and truncated
    with pytest.raises(ValueError, match="state limit"):
        bounded_simple_paths(graph, 0, 2, max_states=0)


def test_shortest_paths_blocked_edges_zero_cost_and_waypoints():
    graph = sample_graph()
    profile = CostProfile(distance=1, time=0, fuel=0, difficulty=0, obstacle=0)
    dijkstra = shortest_path(graph, 0, 2, profile)
    astar = shortest_path(graph, 0, 2, profile, "astar")
    assert dijkstra.vertices == astar.vertices == [0, 1, 2]
    assert dijkstra.cost == pytest.approx(astar.cost)
    graph.edges[1].status = "blocked"
    assert shortest_path(graph, 0, 2, profile).vertices == [0, 2]
    assert shortest_path(graph, 0, 4, profile).cost == inf
    assert shortest_path(graph, 0, 0, profile).vertices == [0]
    assert checkpoint_route(graph, 0, [1, 2], profile).vertices == [0, 1, 0, 2]
    assert shortest_path(graph, 0, 2, CostProfile(0, 0, 0, 0, 0), "astar").cost == 0


def test_heap_handles_duplicates_and_empty():
    heap = MinHeap()
    for value in [4, 1, 2, 1, 9, 0]:
        heap.push(value)
    assert [heap.pop() for _ in range(6)] == [0, 1, 1, 2, 4, 9]
    with pytest.raises(IndexError):
        heap.pop()


def test_knapsack_matches_exhaustive_and_greedy_counterexample():
    items = [Pickup(0, 6, 30), Pickup(1, 5, 24), Pickup(2, 5, 24), Pickup(3, 0, 2)]
    optimal = knapsack(items, 10)
    exhaustive = max(sum(x.benefit for x in group)
                     for size in range(len(items) + 1) for group in combinations(items, size)
                     if sum(x.cost for x in group) <= 10)
    assert optimal.benefit == exhaustive == 50
    assert greedy(items, 10).benefit == 32
    assert knapsack([Pickup(0, 0, 7)], 0).benefit == 7


@pytest.mark.parametrize("items,budget", [
    ([Pickup(0, 6, 30), Pickup(1, 5, 24), Pickup(2, 5, 24)], 10),
    ([Pickup(0, 4, 12), Pickup(1, 3, 8), Pickup(2, 3, 8)], 6),
    ([Pickup(0, 5, 20), Pickup(1, 4, 15), Pickup(2, 4, 15)], 8),
])
def test_greedy_counterexamples_and_exact_dp(items, budget):
    expected = max(sum(item.benefit for item in subset)
                   for count in range(len(items) + 1) for subset in combinations(items, count)
                   if sum(item.cost for item in subset) <= budget)
    assert knapsack(items, budget).benefit == expected
    assert greedy(items, budget).benefit < expected


def test_resource_validation_and_exact_ratio_ties():
    with pytest.raises(ValueError, match="integers"):
        Pickup(1, 1.5, 2)
    with pytest.raises(ValueError, match="unique"):
        knapsack([Pickup(1, 1, 2), Pickup(1, 1, 3)], 3)
    with pytest.raises(ValueError, match="integer"):
        greedy([], 1.5)
    with pytest.raises(ValueError, match="boolean"):
        refuel_plan([1], [1], 1)
    selected = greedy([Pickup(9, 2, 4), Pickup(2, 3, 6), Pickup(1, 0, 1)], 3)
    assert [item.id for item in selected.items] == [1, 2]


def test_refuelling_plan_and_infeasible_route():
    time, purchases = refuel_plan([4, 6], [False, True], 5, capacity=10, max_purchase=5)
    assert time == 5 and purchases == [0, 5]
    assert refuel_plan([11], [True], 0, capacity=10) is None
    assert refuel_plan([1], [False], 0) is None


def test_route_refuelling_uses_conservative_discrete_fuel():
    graph = Graph()
    graph.add_vertex(Vertex(0, 0, 0))
    graph.add_vertex(Vertex(1, 1, 0, kind="fuel"))
    graph.add_vertex(Vertex(2, 2, 0))
    graph.add_edge(Edge(0, 0, 1, 1, 1, 5))
    graph.add_edge(Edge(1, 1, 2, 1, 1, 5))
    assert route_refuelling(graph, [0, 1, 2], [0, 1], fuel=6) == (3, [0, 40])
    assert route_refuelling(graph, [0, 1, 2], [0, 1], fuel=4) is None


@pytest.mark.parametrize("values", [[], [1], [3, 1, 3, 0], list(range(30)), list(range(30, 0, -1))])
def test_sorting_and_top_k_agree(values):
    expected = sorted(values)
    assert merge_sort(values) == quick_sort(values) == heap_sort(values) == expected
    assert top_k(values, 3) == expected[:3]


def test_random_astar_matches_dijkstra():
    rng = Random(47)
    for _ in range(20):
        graph = Graph()
        for vertex in range(10):
            graph.add_vertex(Vertex(vertex, rng.random() * 10, rng.random() * 10))
        for edge_id in range(25):
            a, b = rng.sample(range(10), 2)
            graph.add_edge(Edge(edge_id, a, b, rng.random() * 10, 1, 1, directed=bool(edge_id % 2)))
        costs = {vertex: inf for vertex in graph.vertices}
        costs[0] = 0
        profile = CostProfile()
        for _ in range(len(graph.vertices) - 1):
            for source in graph.vertices:
                for target, edge in graph.neighbors(source):
                    costs[target] = min(costs[target], costs[source] + profile.cost(edge))
        assert shortest_path(graph, 0, 9).cost == pytest.approx(costs[9])
        assert shortest_path(graph, 0, 9, algorithm="astar").cost == pytest.approx(costs[9])


def test_kruskal_rejects_disconnected_graph():
    graph = sample_graph()
    graph.edges[3].directed = False
    with pytest.raises(ValueError, match="disconnected"):
        kruskal(graph)
    graph.add_edge(Edge(4, 3, 4, 1, 1, 1))
    assert len(kruskal(graph)) == 4


def test_checkpoint_route_avoids_future_checkpoints():
    graph = Graph()
    for vertex in range(4):
        graph.add_vertex(Vertex(vertex, vertex, 0))
    for edge in (Edge(0, 0, 2, 1, 1, 1), Edge(1, 2, 1, 1, 1, 1),
                 Edge(2, 0, 3, 3, 3, 3), Edge(3, 3, 1, 3, 3, 3)):
        graph.add_edge(edge)
    route = checkpoint_route(graph, 0, [1, 2])
    assert route.vertices == [0, 3, 1, 2]


def test_directed_traversal_components_cycles_and_bounded_paths():
    graph = Graph()
    for vertex in range(5):
        graph.add_vertex(Vertex(vertex, vertex, 0))
    graph.add_edge(Edge(0, 0, 1, 1, 1, 1, directed=True))
    graph.add_edge(Edge(1, 1, 2, 1, 1, 1, directed=True))
    graph.add_edge(Edge(2, 0, 2, 1, 1, 1, directed=True))
    graph.add_edge(Edge(3, 3, 4, 1, 1, 1, directed=True))
    assert not has_cycle(graph)
    assert len(weak_components(graph)) == 2
    assert bfs(graph, 2).order == [2]
    assert simple_paths(graph, 0, 2, max_length=2) == [[0, 2]]
    with pytest.raises(ValueError, match="positive"):
        simple_paths(graph, 0, 2, max_length=0)
    graph.add_edge(Edge(4, 2, 0, 1, 1, 1, directed=True))
    assert has_cycle(graph)


def test_championship_sorts_and_top_k_use_all_tie_breakers():
    entries = [
        ChampionshipEntry(7, "F", 40, 1, 10, 12),
        ChampionshipEntry(6, "E", 40, 2, 12, 12),
        ChampionshipEntry(5, "D", 40, 2, 10, 14),
        ChampionshipEntry(4, "C", 40, 2, 10, 12),
        ChampionshipEntry(3, "B", 40, 2, 10, 12),
        ChampionshipEntry(2, "A", 41, 0, 20, 20),
    ]
    expected = [2, 3, 4, 5, 6, 7]
    for sort in (merge_sort, quick_sort, heap_sort):
        assert [entry.racer_id for entry in sort(entries, key=ranking_key)] == expected
    assert [entry.racer_id for entry in top_k(entries, 3, key=ranking_key)] == expected[:3]
