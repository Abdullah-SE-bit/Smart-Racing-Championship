"""Shortest paths with a shared manual heap and observable steps."""

from dataclasses import dataclass, field
from math import hypot, inf

from smart_racing.algorithms.structures.heap import IndexedMinHeap
from smart_racing.core.graph import CostProfile, Graph


@dataclass(slots=True)
class Route:
    vertices: list[int] = field(default_factory=list)
    edges: list[int] = field(default_factory=list)
    cost: float = inf
    expanded: int = 0
    relaxed: int = 0
    heap_operations: int = 0
    trace: list[dict] = field(default_factory=list)


def shortest_path(graph: Graph, start: int, target: int,
                  profile: CostProfile | None = None, algorithm: str = "dijkstra",
                  avoid_vertices: set[int] | None = None) -> Route:
    if start not in graph.vertices or target not in graph.vertices:
        raise ValueError("Unknown vertex")
    if algorithm not in {"dijkstra", "astar"}:
        raise ValueError("Unknown routing algorithm")
    profile = profile or CostProfile()
    # The smallest cost per geometric unit proves a consistent lower bound even
    # when road lengths do not equal the distance between their endpoints.
    ratios = []
    for edge in graph.edges.values():
        if edge.status == "blocked":
            continue
        a, b = graph.vertices[edge.source], graph.vertices[edge.target]
        geometric = hypot(a.x - b.x, a.y - b.y)
        if geometric:
            ratios.append(profile.cost(edge) / geometric)
    ratio = min(ratios, default=0.0) if algorithm == "astar" else 0.0
    destination = graph.vertices[target]

    def heuristic(vertex):
        position = graph.vertices[vertex]
        return ratio * hypot(position.x - destination.x, position.y - destination.y)

    queue = IndexedMinHeap()
    queue.push_or_decrease((heuristic(start), 0.0, start))
    distances = {start: 0.0}
    parents = {}
    result = Route()
    while queue:
        _, distance, vertex = queue.pop()
        result.expanded += 1
        result.trace.append({"action": "expand", "vertex": vertex, "cost": distance})
        if vertex == target:
            result.cost = distance
            break
        for neighbor, edge in graph.neighbors(vertex):
            result.relaxed += 1
            if avoid_vertices and neighbor in avoid_vertices and neighbor != target:
                continue
            candidate = distance + profile.cost(edge)
            if candidate < distances.get(neighbor, inf):
                distances[neighbor] = candidate
                parents[neighbor] = (vertex, edge.id)
                queue.push_or_decrease((candidate + heuristic(neighbor), candidate, neighbor))
                result.trace.append({"action": "relax", "vertex": neighbor, "edge": edge.id, "cost": candidate})
    result.heap_operations = queue.operations
    if result.cost != inf:
        vertex = target
        result.vertices.append(vertex)
        while vertex != start:
            vertex, edge_id = parents[vertex]
            result.vertices.append(vertex)
            result.edges.append(edge_id)
        result.vertices.reverse()
        result.edges.reverse()
    return result


def checkpoint_route(graph: Graph, start: int, checkpoints: list[int],
                     profile: CostProfile | None = None, algorithm: str = "dijkstra") -> Route:
    combined = Route(vertices=[start], cost=0.0)
    for index, target in enumerate(checkpoints):
        # A leg cannot pass a later mandatory checkpoint before its turn.
        future = set(checkpoints[index + 1:]) - {target}
        leg = shortest_path(graph, combined.vertices[-1], target, profile, algorithm, future)
        combined.expanded += leg.expanded
        combined.relaxed += leg.relaxed
        combined.heap_operations += leg.heap_operations
        combined.trace.extend(leg.trace)
        if not leg.vertices:
            combined.vertices.clear()
            combined.edges.clear()
            combined.cost = inf
            return combined
        combined.vertices.extend(leg.vertices[1:])
        combined.edges.extend(leg.edges)
        combined.cost += leg.cost
    return combined
