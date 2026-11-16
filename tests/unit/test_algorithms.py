from itertools import combinations, product
from math import inf
from random import Random

import pytest

from smart_racing.algorithms.generation.mst import kruskal
from smart_racing.algorithms.graph.traversal import bfs, bounded_simple_paths, dead_ends, dfs, has_cycle, simple_paths, weak_components
from smart_racing.algorithms.optimization.resources import Pickup, greedy, knapsack, refuel_plan
from smart_racing.algorithms.routing.shortest import checkpoint_route, shortest_path
from smart_racing.algorithms.sorting.rankings import heap_sort, merge_sort, quick_sort, top_k
from smart_racing.algorithms.structures.heap import IndexedMinHeap, MinHeap
from smart_racing.core.graph import CostProfile, Edge, Graph, Vertex
from smart_racing.resources.planner import pickup_suggestions, route_refuelling
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


def test_cycle_detection_handles_mixed_parallel_roads_and_closures():
    graph = Graph()
    graph.add_vertex(Vertex(0, 0, 0))
    graph.add_vertex(Vertex(1, 1, 0))
    graph.add_edge(Edge(0, 0, 1, 1, 1, 1))
    assert not has_cycle(graph)
    graph.add_edge(Edge(1, 0, 1, 1, 1, 1, directed=True))
    assert has_cycle(graph)
    graph.edges[1].status = "blocked"
    assert not has_cycle(graph)


def test_mixed_cycle_detection_matches_exhaustive_small_graphs():
    def exhaustive(graph):
        def search(start, current, visited, used_roads):
            for neighbor, road in graph.neighbors(current):
                if road.id in used_roads:
                    continue
                if neighbor == start:
                    return True
                if neighbor not in visited and search(start, neighbor, visited | {neighbor}, used_roads | {road.id}):
                    return True
            return False
        return any(search(start, start, {start}, set()) for start in graph.vertices)

    rng = Random(20261205)
    for _ in range(300):
        graph = Graph()
        for vertex in range(4):
            graph.add_vertex(Vertex(vertex, vertex, 0))
        for road_id in range(rng.randrange(9)):
            graph.add_edge(Edge(road_id, rng.randrange(4), rng.randrange(4), 1, 1, 1,
                                status="blocked" if rng.randrange(5) == 0 else "open",
                                directed=bool(rng.randrange(2))))
        assert has_cycle(graph) == exhaustive(graph)


def test_weak_components_handle_isolated_vertices_and_mixed_roads():
    graph = Graph()
    for vertex in range(2000):
        graph.add_vertex(Vertex(vertex, vertex, 0))
    graph.add_edge(Edge(0, 2, 0, 1, 1, 1, directed=True))
    graph.add_edge(Edge(1, 0, 2, 1, 1, 1))
    graph.add_edge(Edge(2, 2, 3, 1, 1, 1, status="blocked"))
    components = weak_components(graph)
    assert components[0] == [0, 2]
    assert len(components) == 1999
    assert [1] in components and [3] in components
    assert components == weak_components(graph)


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


def test_routing_matches_independent_bellman_ford_on_mixed_graphs():
    """Compare costs and edge paths against a separate relaxation algorithm."""
    def reference(graph, start):
        distances = {vertex: inf for vertex in graph.vertices}
        distances[start] = 0
        for _ in range(len(graph.vertices) - 1):
            updated = False
            for road in graph.edges.values():
                if road.status == "blocked":
                    continue
                directions = [(road.source, road.target)]
                if not road.directed:
                    directions.append((road.target, road.source))
                for source, target in directions:
                    candidate = distances[source] + road.distance
                    if candidate < distances[target]:
                        distances[target] = candidate
                        updated = True
            if not updated:
                break
        return distances

    profile = CostProfile(distance=1, time=0, fuel=0, difficulty=0, obstacle=0,
                          distance_reference=1)
    rng = Random(20261205)
    covered = set()
    for _ in range(160):
        graph = Graph()
        for vertex in range(4):
            graph.add_vertex(Vertex(vertex, rng.randrange(10), rng.randrange(10)))
        for road_id in range(rng.randrange(12)):
            graph.add_edge(Edge(road_id, rng.randrange(4), rng.randrange(4), rng.randrange(6), 1, 1,
                                status="blocked" if rng.randrange(5) == 0 else "open",
                                directed=bool(rng.randrange(2))))
        pairs = set()
        for road in graph.edges.values():
            covered.add("directed" if road.directed else "undirected")
            if road.status == "blocked":
                covered.add("blocked")
            if road.distance == 0:
                covered.add("zero")
            endpoints = frozenset((road.source, road.target))
            if endpoints in pairs:
                covered.add("parallel")
            pairs.add(endpoints)
        for start in graph.vertices:
            distances = reference(graph, start)
            for target in graph.vertices:
                for algorithm in ("dijkstra", "astar"):
                    route = shortest_path(graph, start, target, profile, algorithm)
                    assert route.cost == distances[target]
                    if route.cost == inf:
                        covered.add("unreachable")
                        assert not route.vertices and not route.edges
                        continue
                    assert route.vertices[0] == start and route.vertices[-1] == target
                    assert len(route.edges) + 1 == len(route.vertices)
                    for source, destination, road_id in zip(route.vertices, route.vertices[1:], route.edges):
                        assert any(neighbor == destination and road.id == road_id
                                   for neighbor, road in graph.neighbors(source))
                    assert sum(graph.edges[road].distance for road in route.edges) == route.cost
    assert covered == {"directed", "undirected", "blocked", "zero", "parallel", "unreachable"}


@pytest.mark.parametrize("algorithm", ["dijkstra", "astar"])
def test_equal_cost_ties_and_replanning_after_road_updates(algorithm):
    graph = Graph()
    for vertex in range(4):
        graph.add_vertex(Vertex(vertex, vertex, 0))
    for edge in (Edge(0, 0, 1, 1, 1, 1), Edge(1, 1, 3, 1, 1, 1),
                 Edge(2, 0, 2, 1, 1, 1), Edge(3, 2, 3, 1, 1, 1)):
        graph.add_edge(edge)
    profile = CostProfile(distance=0, time=1, fuel=0, difficulty=0, obstacle=0, time_reference=1)
    first = shortest_path(graph, 0, 3, profile, algorithm)
    assert first.vertices in ([0, 1, 3], [0, 2, 3]) and first.cost == 2
    assert shortest_path(graph, 0, 3, profile, algorithm).vertices == first.vertices
    assert first.expanded > 0 and first.relaxed > 0 and first.heap_operations > 0
    graph.edges[1].status = "restricted"
    assert shortest_path(graph, 0, 3, profile, algorithm).vertices == [0, 2, 3]
    graph.edges[3].status = "blocked"
    rerouted = shortest_path(graph, 0, 3, profile, algorithm)
    assert rerouted.vertices == [0, 1, 3] and rerouted.cost == 2.5
    graph.edges[1].status = "blocked"
    assert shortest_path(graph, 0, 3, profile, algorithm).vertices == []


def test_heap_handles_duplicates_and_empty():
    heap = MinHeap()
    for value in [4, 1, 2, 1, 9, 0]:
        heap.push(value)
    assert [heap.pop() for _ in range(6)] == [0, 1, 1, 2, 4, 9]
    with pytest.raises(IndexError):
        heap.pop()
    with pytest.raises(IndexError):
        heap.peek()


def test_indexed_heap_tracks_decreases_and_never_duplicates_vertices():
    rng = Random(20261205)
    heap = IndexedMinHeap()
    expected = {}
    for _ in range(500):
        if expected and rng.randrange(4) == 0:
            item = heap.pop()
            assert item == min(expected.values())
            del expected[item[2]]
        else:
            vertex = rng.randrange(30)
            if vertex in expected:
                old = expected[vertex]
                item = (old[0] - 1, old[1] - 1, vertex)
            else:
                value = rng.randrange(100)
                item = (value, value, vertex)
            heap.push_or_decrease(item)
            expected[vertex] = item
        assert len(heap) == len(expected) <= 30
    while expected:
        item = heap.pop()
        assert item == min(expected.values())
        del expected[item[2]]
    with pytest.raises(IndexError):
        heap.pop()
    heap.push_or_decrease((1, 1, 4))
    with pytest.raises(ValueError, match="decrease"):
        heap.push_or_decrease((2, 2, 4))


def test_routing_decreases_one_vertex_key_for_many_parallel_roads():
    graph = Graph()
    graph.add_vertex(Vertex(0, 0, 0))
    graph.add_vertex(Vertex(1, 1, 0))
    for road_id in range(100):
        graph.add_edge(Edge(road_id, 0, 1, 100 - road_id, 1, 1, directed=True))
    profile = CostProfile(distance=1, time=0, fuel=0, difficulty=0, obstacle=0,
                          distance_reference=1)
    route = shortest_path(graph, 0, 1, profile)
    assert route.cost == 1 and route.edges == [99]
    assert route.relaxed == 100
    assert route.heap_operations == 103  # start insertion, 100 updates, two extractions


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


def test_refuelling_dp_matches_exhaustive_small_routes():
    capacity, purchase_limit, stop_time = 4, 2, 3
    for requirements in product(range(4), repeat=3):
        for available in product((False, True), repeat=3):
            for initial in range(capacity + 1):
                feasible = []
                for purchases in product(range(purchase_limit + 1), repeat=3):
                    fuel = initial
                    for required, station, amount in zip(requirements, available, purchases):
                        if (amount and not station) or fuel + amount > capacity:
                            break
                        fuel += amount - required
                        if fuel < 0:
                            break
                    else:
                        feasible.append(sum(stop_time for amount in purchases if amount))
                result = refuel_plan(list(requirements), list(available), initial,
                                     capacity, purchase_limit, stop_time)
                if not feasible:
                    assert result is None
                else:
                    assert result is not None and result[0] == min(feasible)
                    fuel = initial
                    for required, station, amount in zip(requirements, available, result[1]):
                        assert 0 <= amount <= purchase_limit and (station or amount == 0)
                        assert fuel + amount <= capacity
                        fuel += amount - required
                        assert fuel >= 0


def test_ordered_pickup_suggestions_do_not_pass_later_checkpoints_early():
    graph = Graph()
    for vertex in (Vertex(0, 0, 0, "start"), Vertex(1, 1, 0, "checkpoint", 1),
                   Vertex(2, 2, 0, "checkpoint", 2), Vertex(3, 3, 0, "nitro"),
                   Vertex(4, 1, 1, "nitro")):
        graph.add_vertex(vertex)
    for edge in (Edge(0, 0, 1, 1, 1, 1, directed=True),
                 Edge(1, 1, 2, 1, 1, 1, directed=True),
                 Edge(2, 0, 2, 1, 1, 1, directed=True),
                 Edge(3, 2, 3, 1, 1, 1, directed=True),
                 Edge(4, 3, 1, 1, 1, 1, directed=True),
                 Edge(5, 1, 4, 1, 1, 1, directed=True),
                 Edge(6, 4, 2, 1, 1, 1, directed=True)):
        graph.add_edge(edge)
    suggestions = pickup_suggestions(graph, 0, 2, waypoints=[1, 2])
    assert [suggestion.vertex for suggestion in suggestions] == [4]
    assert suggestions[0].dp_selected


def test_pickup_suggestions_account_for_other_pickups_filling_nitro_capacity():
    graph = Graph()
    for vertex in (Vertex(0, 0, 0, "start"), Vertex(1, 1, 0, "nitro"),
                   Vertex(2, 2, 0, "nitro"), Vertex(3, 3, 0, "finish")):
        graph.add_vertex(vertex)
    for index in range(3):
        graph.add_edge(Edge(index, index, index + 1, 1, 1, 1, directed=True))
    suggestions = pickup_suggestions(graph, 0, 3, nitro=2)
    assert [suggestion.vertex for suggestion in suggestions] == [1]


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
    with pytest.raises(ValueError, match="undirected"):
        kruskal(graph)
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


def test_merge_and_quick_sort_preserve_equal_key_input_order():
    values = [(1, "first"), (0, "lower"), (1, "second"), (1, "third")]
    for method in (merge_sort, quick_sort):
        assert method(values, key=lambda item: item[0]) == [values[1], values[0], values[2], values[3]]
