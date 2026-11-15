"""Load authored circuit data and check its essential graph constraints."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from smart_racing.algorithms.graph.traversal import bfs, dead_ends, has_cycle, ordered_lap_paths
from smart_racing.algorithms.routing.shortest import checkpoint_route
from smart_racing.core.graph import Edge, Graph, Vertex


@dataclass(slots=True)
class Circuit:
    name: str
    graph: Graph
    start: int
    checkpoints: list[int]
    main_route: list[int]


def save_circuit(circuit: Circuit, path: str | Path) -> None:
    errors = validate_circuit(circuit)
    if errors:
        raise ValueError("Invalid circuit: " + "; ".join(errors))
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = {"name": circuit.name, "start": circuit.start, "checkpoints": circuit.checkpoints,
            "main_route": circuit.main_route,
            "vertices": [asdict(vertex) for vertex in circuit.graph.vertices.values()],
            "edges": [asdict(edge) for edge in circuit.graph.edges.values()]}
    destination.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_circuit(path: str | Path) -> Circuit:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    graph = Graph()
    for vertex in data["vertices"]:
        graph.add_vertex(Vertex(**vertex))
    for edge in data["edges"]:
        graph.add_edge(Edge(**edge))
    circuit = Circuit(data["name"], graph, data["start"], data["checkpoints"], data["main_route"])
    errors = validate_circuit(circuit)
    if errors:
        raise ValueError("Invalid circuit: " + "; ".join(errors))
    return circuit


def validate_circuit(circuit: Circuit) -> list[str]:
    graph = circuit.graph
    errors = []
    if circuit.start not in graph.vertices:
        return ["start vertex does not exist"]
    if len(circuit.checkpoints) < 10 or len(set(circuit.checkpoints)) != len(circuit.checkpoints):
        errors.append("at least ten distinct checkpoints are required")
    if any(vertex not in graph.vertices for vertex in circuit.checkpoints):
        errors.append("checkpoint vertex does not exist")
        return errors
    for order, vertex_id in enumerate(circuit.checkpoints, 1):
        vertex = graph.vertices[vertex_id]
        if vertex.kind != "checkpoint" or vertex.checkpoint_order != order:
            errors.append(f"checkpoint {vertex_id} has incorrect order")
    if sum(edge.shortcut for edge in graph.edges.values()) < 2:
        errors.append("at least two shortcuts are required")
    if not any(edge.obstacle > 0 for edge in graph.edges.values()):
        errors.append("at least one obstacle is required")
    for source, target in zip([circuit.start] + circuit.checkpoints,
                              circuit.checkpoints + [circuit.start]):
        if target not in bfs(graph, source).parents:
            errors.append(f"{target} is unreachable from {source}")
    ordered_route = checkpoint_route(graph, circuit.start, circuit.checkpoints + [circuit.start])
    if not ordered_route.vertices:
        errors.append("ordered checkpoint route or lap return is infeasible")
    else:
        routes, truncated = ordered_lap_paths(graph, circuit.start, circuit.checkpoints)
        if len(routes) < 2:
            errors.append("ordered alternatives could not be verified within the search limit" if truncated
                          else "at least two simple ordered checkpoint laps are required")
    for kind in ("fuel", "nitro", "dead_end"):
        if not any(vertex.kind == kind for vertex in graph.vertices.values()):
            errors.append(f"missing {kind} vertex")
    if not has_cycle(graph):
        errors.append("at least one cycle is required")
    if not dead_ends(graph, circuit.start):
        errors.append("at least one dead end is required")
    if sum(len(list(graph.neighbors(v))) >= 3 for v in graph.vertices) < 2:
        errors.append("multiple intersections are required")
    if not circuit.main_route or circuit.main_route[0] != circuit.start or circuit.main_route[-1] != circuit.start:
        errors.append("main route must begin and end at start")
    elif any(not any(neighbor == target for neighbor, _ in graph.neighbors(source))
             for source, target in zip(circuit.main_route, circuit.main_route[1:])):
        errors.append("main route contains a missing or blocked road")
    else:
        encountered = [vertex for vertex in circuit.main_route if vertex in circuit.checkpoints]
        if encountered != circuit.checkpoints:
            errors.append("main route must visit checkpoints in order")
        fuel = 100.0
        for source, target in zip(circuit.main_route, circuit.main_route[1:]):
            vertex = graph.vertices[source]
            if vertex.kind == "fuel" and vertex.active:
                fuel = min(100.0, fuel + 40.0)
            edge = next(edge for neighbor, edge in graph.neighbors(source) if neighbor == target)
            fuel -= edge.fuel_cost * (1 + .1 * (edge.difficulty - 1))
            if fuel < -1e-9:
                errors.append("main route has no feasible full-tank fuel plan")
                break
    return errors
