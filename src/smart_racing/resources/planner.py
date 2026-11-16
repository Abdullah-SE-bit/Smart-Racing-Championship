"""Feasible single-pickup recommendations using shared resource algorithms."""

from dataclasses import dataclass
from math import ceil, floor

from smart_racing.algorithms.optimization.resources import Pickup, greedy, knapsack, refuel_plan
from smart_racing.algorithms.routing.shortest import checkpoint_route
from smart_racing.core.graph import CostProfile, Graph


@dataclass(slots=True)
class PickupSuggestion:
    vertex: int
    detour: int
    fuel_needed: float
    benefit: int
    dp_selected: bool
    greedy_selected: bool


def route_refuelling(graph: Graph, vertices: list[int], edges: list[int], fuel: float = 100):
    """Plan a route using tenths of a fuel unit and conservative rounding.

    The returned purchases are tenths of a unit at the corresponding route
    vertices. Edge requirements round up and starting fuel rounds down, so a
    reported feasible plan cannot rely on fuel that is not actually available.
    """
    if len(vertices) != len(edges) + 1 or not 0 <= fuel <= 100:
        raise ValueError("Invalid route or starting fuel")
    costs = []
    for source, target, edge_id in zip(vertices, vertices[1:], edges):
        edge = graph.edges[edge_id]
        if not any(neighbor == target and road.id == edge_id for neighbor, road in graph.neighbors(source)):
            raise ValueError("Route contains an unavailable road")
        costs.append(ceil(edge.fuel_cost * (1 + .1 * (edge.difficulty - 1)) * 10 - 1e-9))
    stations = [graph.vertices[vertex].kind == "fuel" and graph.vertices[vertex].active
                for vertex in vertices[:-1]]
    return refuel_plan(costs, stations, floor(fuel * 10), capacity=1000, max_purchase=400, stop_time=3)


def pickup_suggestions(graph: Graph, start: int, target: int, fuel: float = 100,
                       nitro: int = 1, budget: int = 10,
                       waypoints: list[int] | None = None) -> list[PickupSuggestion]:
    """Evaluate active nitro pickups independently against a distance budget.

    Recommendations are single-pickup alternatives, so a combined route never
    silently exceeds the fuel tank or nitro capacity. A pickup's cost is the
    rounded-up extra road distance compared with the distance route through
    the same ordered waypoints. Without waypoints the target is an endpoint.
    """
    if fuel < 0 or nitro < 0 or budget < 0:
        raise ValueError("Invalid resource state")
    if nitro >= 3:
        return []
    profile = CostProfile(distance=1, time=0, fuel=0, difficulty=0, obstacle=0,
                          distance_reference=1)
    destinations = list(waypoints) if waypoints is not None else [target]
    if not destinations or destinations[-1] != target:
        raise ValueError("The last waypoint must be the target")
    baseline = checkpoint_route(graph, start, destinations, profile)
    if not baseline.vertices:
        return []
    suggestions = []
    for vertex in graph.vertices.values():
        if vertex.kind != "nitro" or not vertex.active:
            continue
        candidates = []
        for index in range(len(destinations)):
            candidate = checkpoint_route(graph, start,
                                         destinations[:index] + [vertex.id] + destinations[index:], profile)
            if candidate.vertices:
                candidates.append(candidate)
        if not candidates:
            continue
        feasible = []
        for candidate in candidates:
            fuel_needed = sum(graph.edges[edge_id].fuel_cost * (1 + .1 * (graph.edges[edge_id].difficulty - 1))
                              for edge_id in candidate.edges)
            charges = nitro
            collected = set()
            for visited in candidate.vertices[1:]:
                service = graph.vertices[visited]
                if service.kind == "nitro" and service.active and visited not in collected and charges < 3:
                    collected.add(visited)
                    charges += 1
            if fuel_needed <= fuel and vertex.id in collected:
                feasible.append((candidate.cost, fuel_needed, candidate.vertices, candidate.edges))
        if not feasible:
            continue
        distance, fuel_needed, _, _ = min(feasible)
        detour = max(0, ceil(distance - baseline.cost - 1e-9))
        # A separate one-item choice avoids treating independent alternative
        # routes as if their distances or fuel costs were additive.
        item = Pickup(vertex.id, detour, 1)
        dp = knapsack([item], budget)
        heuristic = greedy([item], budget)
        suggestions.append(PickupSuggestion(vertex.id, detour, fuel_needed, 1,
                                            bool(dp.items), bool(heuristic.items)))
    return suggestions
