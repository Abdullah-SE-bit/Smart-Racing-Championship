"""Seeded circuit generation using an MST and backtracking placement."""

from math import cos, hypot, pi, sin
from random import Random

from smart_racing.algorithms.generation.mst import kruskal
from smart_racing.core.graph import Edge, Graph, Vertex
from smart_racing.tracks.circuits import Circuit, validate_circuit


def _assign_checkpoints(candidates: list[int], count: int, trace: list[dict] | None = None,
                        compatible=None) -> list[int] | None:
    """Choose distinct positions subject to a placement constraint.

    Each candidate can be attempted in any order. The optional predicate sees the
    partial placement and may reject a candidate before exploring its subtree.
    """
    chosen = []
    used = set()

    def place():
        if len(chosen) == count:
            return True
        if len(candidates) - len(used) < count - len(chosen):
            return False
        for candidate in candidates:
            if candidate in used:
                continue
            if compatible is not None and not compatible(chosen, candidate):
                if trace is not None:
                    trace.append({"action": "reject placement", "vertex": candidate, "value": len(chosen)})
                continue
            chosen.append(candidate)
            used.add(candidate)
            if trace is not None:
                trace.append({"action": "place checkpoint", "vertex": candidate, "value": len(chosen)})
            if place():
                return True
            chosen.pop()
            used.remove(candidate)
            if trace is not None:
                trace.append({"action": "backtrack", "vertex": candidate, "value": len(chosen)})
        return False

    return chosen.copy() if place() else None


def _ring_compatible(chosen: list[int], candidate: int) -> bool:
    # The start (0) is adjacent to ring positions 1 and 10. Each next
    # checkpoint must be adjacent to the previous one on the authored loop.
    return candidate in {1, 10} if not chosen else abs(candidate - chosen[-1]) == 1


def _place_obstacles(graph: Graph, main_route: list[int], count: int = 2) -> list[int] | None:
    """Place spaced obstacles on non-bridge roads outside the main loop.

    Excluding bridges ensures an obstacle could later close its road without
    disconnecting its endpoints. Edge-disjoint placements keep obstacles apart.
    """
    main_pairs = {frozenset((a, b)) for a, b in zip(main_route, main_route[1:])}

    def is_non_bridge(edge):
        stack = [edge.source]
        visited = {edge.source}
        while stack:
            vertex = stack.pop()
            for neighbor, candidate in graph.neighbors(vertex):
                if candidate.id != edge.id and neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        return edge.target in visited

    candidates = [edge.id for edge in graph.edges.values()
                  if not edge.shortcut and 13 not in (edge.source, edge.target)
                  and frozenset((edge.source, edge.target)) not in main_pairs and is_non_bridge(edge)]

    def separated(chosen, edge_id):
        edge = graph.edges[edge_id]
        endpoints = {edge.source, edge.target}
        return all(not endpoints.intersection({graph.edges[other].source, graph.edges[other].target})
                   for other in chosen)

    return _assign_checkpoints(candidates, count, compatible=separated)


def _generate_candidate(seed: int, attempt: int, trace: list[dict] | None = None) -> Circuit:
    rng = Random(seed if attempt == 0 else f"{seed}:{attempt}")
    graph = Graph()
    candidates = list(range(1, 11))
    rng.shuffle(candidates)
    checkpoints = _assign_checkpoints(candidates, 10, compatible=_ring_compatible)
    if checkpoints is None:
        raise ValueError("Unable to place ordered checkpoints on the loop")
    if trace is not None:
        trace.append({"stage": "checkpoints", "detail": f"Placed {len(checkpoints)} ordered checkpoints"})
    for vertex_id in range(11):
        angle = 2 * pi * vertex_id / 11 - pi / 2
        radius = rng.uniform(.86, 1.06)
        graph.add_vertex(Vertex(vertex_id, 500 + 320 * radius * cos(angle),
                                350 + 230 * radius * sin(angle),
                                "start" if vertex_id == 0 else "checkpoint",
                                None if vertex_id == 0 else checkpoints.index(vertex_id) + 1))
    service_locations = {11: (410, 250), 12: (610, 430), 14: (500, 350), 15: (530, 250)}
    service_candidates = list(service_locations)
    rng.shuffle(service_candidates)

    def services_spaced(chosen, candidate):
        x, y = service_locations[candidate]
        return all(hypot(x - service_locations[other][0], y - service_locations[other][1]) >= 120
                   for other in chosen)

    services = _assign_checkpoints(service_candidates, 2, compatible=services_spaced)
    if services is None:
        raise ValueError("Unable to place spaced fuel and nitro services")
    fuel_vertex, nitro_vertex = services
    if trace is not None:
        trace.append({"stage": "services", "detail": f"Fuel {fuel_vertex}, nitro {nitro_vertex}; spacing checked"})
    graph.add_vertex(Vertex(13, 180, 300, "dead_end"))
    for vertex_id, (x, y) in service_locations.items():
        kind = "fuel" if vertex_id == fuel_vertex else "nitro" if vertex_id == nitro_vertex else "intersection"
        graph.add_vertex(Vertex(vertex_id, x, y, kind))

    candidate = Graph()
    for vertex in graph.vertices.values():
        if vertex.id != 13:
            candidate.add_vertex(vertex)
    candidate_id = 0
    ids = sorted(candidate.vertices)
    for index, a in enumerate(ids):
        for b in ids[index + 1:]:
            first, second = graph.vertices[a], graph.vertices[b]
            distance = hypot(first.x - second.x, first.y - second.y) / 20
            candidate.add_edge(Edge(candidate_id, a, b, distance, distance / 8, distance / 15))
            candidate_id += 1
    pairs = {(min(candidate.edges[e].source, candidate.edges[e].target),
              max(candidate.edges[e].source, candidate.edges[e].target)) for e in kruskal(candidate)}
    if trace is not None:
        trace.append({"stage": "backbone", "detail": f"Kruskal selected {len(pairs)} candidate roads"})
    # Add a guaranteed lap cycle, service alternatives and a single dead end.
    pairs.update((min(i, (i + 1) % 11), max(i, (i + 1) % 11)) for i in range(11))
    pairs.update({(2, fuel_vertex), (3, fuel_vertex), (6, nitro_vertex),
                  (7, nitro_vertex), (4, 13)})
    shortcut_pairs = {(3, fuel_vertex), (7, nitro_vertex)}
    if trace is not None:
        trace.append({"stage": "roads", "detail": f"Added lap and alternatives: {len(pairs)} roads"})
    for edge_id, (a, b) in enumerate(sorted(pairs)):
        first, second = graph.vertices[a], graph.vertices[b]
        length = hypot(first.x - second.x, first.y - second.y) / 20
        graph.add_edge(Edge(edge_id, a, b, length, length / 8, length / 15,
                            difficulty=1 + edge_id % 4, shortcut=(a, b) in shortcut_pairs))
    main_route = [0] + checkpoints + [0]
    obstacles = _place_obstacles(graph, main_route)
    if obstacles is None:
        raise ValueError("Unable to place spaced obstacles on non-bridge roads")
    if trace is not None:
        trace.append({"stage": "obstacles", "detail": f"Placed {len(obstacles)} spaced non-bridge obstacles"})
    for edge_id in obstacles:
        graph.edges[edge_id].obstacle = 1.0

    # The MST and lap remain undirected. Add distinct one-way service roads
    # afterwards so directed routing is exercised without changing the backbone.
    occupied = {frozenset((edge.source, edge.target)) for edge in graph.edges.values()}
    directed_candidates = [(source, target) for source in range(11)
                           for target in sorted(service_locations)
                           if frozenset((source, target)) not in occupied]
    rng.shuffle(directed_candidates)
    if len(directed_candidates) < 2:
        raise ValueError("Unable to place one-way roads")
    for source, target in directed_candidates[:2]:
        first, second = graph.vertices[source], graph.vertices[target]
        length = hypot(first.x - second.x, first.y - second.y) / 20
        graph.add_edge(Edge(len(graph.edges), source, target, length, length / 8, length / 15,
                            difficulty=2, directed=True))
    if trace is not None:
        trace.append({"stage": "one_way", "detail": "Added 2 one-way roads after the MST"})
    return Circuit(f"Generated {seed}", graph, 0, checkpoints, main_route)


def generate_circuit(seed: int, max_attempts: int = 5, trace: list[dict] | None = None) -> Circuit:
    """Generate and validate deterministic candidates up to a bounded limit."""
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("Seed must be an integer")
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or max_attempts < 1:
        raise ValueError("Maximum attempts must be a positive integer")
    last_error = "no candidate"
    for attempt in range(max_attempts):
        try:
            if trace is not None:
                trace.append({"stage": "attempt", "detail": f"Seed {seed}, attempt {attempt + 1}"})
                circuit = _generate_candidate(seed, attempt, trace)
            else:
                circuit = _generate_candidate(seed, attempt)
            errors = validate_circuit(circuit)
            if not errors:
                if trace is not None:
                    trace.append({"stage": "accepted", "detail": "Circuit passed validation"})
                return circuit
            last_error = "; ".join(errors)
        except ValueError as error:
            last_error = str(error)
        if trace is not None:
            trace.append({"stage": "rejected", "detail": last_error})
    raise ValueError(f"Could not generate a valid circuit after {max_attempts} attempts: {last_error}")
