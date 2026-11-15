"""Breadth-first and depth-first circuit exploration."""

from collections import deque
from dataclasses import dataclass, field

from smart_racing.core.graph import Graph


@dataclass(slots=True)
class Traversal:
    order: list[int] = field(default_factory=list)
    parents: dict[int, int | None] = field(default_factory=dict)
    examined_edges: int = 0
    trace: list[dict] = field(default_factory=list)

    def path_to(self, target: int) -> list[int]:
        if target not in self.parents:
            return []
        path = []
        current = target
        while current is not None:
            path.append(current)
            current = self.parents[current]
        return path[::-1]


def bfs(graph: Graph, start: int) -> Traversal:
    if start not in graph.vertices:
        raise ValueError("Unknown start vertex")
    result = Traversal(parents={start: None})
    queue = deque([start])
    while queue:
        current = queue.popleft()
        result.order.append(current)
        result.trace.append({"action": "visit", "vertex": current})
        for neighbor, edge in graph.neighbors(current):
            result.examined_edges += 1
            if neighbor not in result.parents:
                result.parents[neighbor] = current
                queue.append(neighbor)
                result.trace.append({"action": "discover", "vertex": neighbor, "edge": edge.id})
    return result


def dfs(graph: Graph, start: int) -> Traversal:
    if start not in graph.vertices:
        raise ValueError("Unknown start vertex")
    result = Traversal(parents={start: None})
    stack = [(start, iter(graph.neighbors(start)))]
    result.order.append(start)
    result.trace.append({"action": "visit", "vertex": start})
    while stack:
        current, neighbors = stack[-1]
        try:
            neighbor, edge = next(neighbors)
        except StopIteration:
            stack.pop()
            continue
        result.examined_edges += 1
        if neighbor not in result.parents:
            result.parents[neighbor] = current
            result.order.append(neighbor)
            result.trace.append({"action": "visit", "vertex": neighbor, "edge": edge.id})
            stack.append((neighbor, iter(graph.neighbors(neighbor))))
    return result


def simple_paths(graph: Graph, start: int, target: int, limit: int = 10,
                 max_length: int | None = None) -> list[list[int]]:
    """Enumerate at most limit simple paths; enumeration can be exponential."""
    if start not in graph.vertices or target not in graph.vertices:
        raise ValueError("Unknown vertex")
    if limit <= 0:
        return []
    max_length = max_length if max_length is not None else len(graph.vertices)
    if max_length < 1:
        raise ValueError("Path length limit must be positive")
    result = []
    path = [start]
    visited = {start}

    def visit(current):
        if current == target:
            result.append(path.copy())
            return
        if len(path) >= max_length:
            return
        for neighbor, _ in graph.neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                visit(neighbor)
                path.pop()
                visited.remove(neighbor)
                if len(result) >= limit:
                    return

    visit(start)
    return result


def ordered_lap_paths(graph: Graph, start: int, checkpoints: list[int], limit: int = 2,
                      max_states: int = 50000) -> tuple[list[list[int]], bool]:
    """Find simple ordered laps, returning edge paths and a search-limit flag.

    A lap may return to the start only after all checkpoints. Other vertices may
    appear once, and future checkpoints cannot be entered out of order. The
    search is exponential in the worst case, so the number of explored states is
    bounded and callers must treat a truncated search as inconclusive.
    """
    if start not in graph.vertices or any(vertex not in graph.vertices for vertex in checkpoints):
        raise ValueError("Unknown lap vertex")
    if limit <= 0 or max_states <= 0:
        raise ValueError("Search limits must be positive")
    if len(set(checkpoints)) != len(checkpoints) or start in checkpoints:
        raise ValueError("Checkpoints must be distinct and different from start")
    checkpoint_set = set(checkpoints)
    visited = {start}
    edges = []
    routes = []
    explored = 0
    truncated = False

    def visit(current, progress):
        nonlocal explored, truncated
        if explored >= max_states:
            truncated = True
            return
        explored += 1
        for neighbor, edge in graph.neighbors(current):
            if neighbor == start:
                if progress == len(checkpoints) and edges:
                    routes.append(edges + [edge.id])
            elif neighbor not in visited:
                next_progress = progress
                if neighbor in checkpoint_set:
                    if progress >= len(checkpoints) or neighbor != checkpoints[progress]:
                        continue
                    next_progress += 1
                visited.add(neighbor)
                edges.append(edge.id)
                visit(neighbor, next_progress)
                edges.pop()
                visited.remove(neighbor)
            if len(routes) >= limit or truncated:
                return

    visit(start, 0)
    return routes, truncated


def weak_components(graph: Graph) -> list[list[int]]:
    """Components ignoring direction, while excluding blocked roads."""
    adjacency = {vertex: set() for vertex in graph.vertices}
    for edge in graph.edges.values():
        if edge.status != "blocked":
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)
    remaining = set(graph.vertices)
    components = []
    while remaining:
        start = min(remaining)
        stack = [start]
        remaining.remove(start)
        component = []
        while stack:
            vertex = stack.pop()
            component.append(vertex)
            for neighbor in sorted(adjacency[vertex], reverse=True):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def has_cycle(graph: Graph) -> bool:
    """Detect directed cycles and undirected cycles, including parallel roads."""
    state = {vertex: 0 for vertex in graph.vertices}

    def visit(vertex, parent_edge):
        state[vertex] = 1
        for neighbor, edge in graph.neighbors(vertex):
            if not edge.directed and edge.id == parent_edge:
                continue
            if state[neighbor] == 1:
                return True
            if state[neighbor] == 0 and visit(neighbor, edge.id):
                return True
        state[vertex] = 2
        return False

    return any(state[vertex] == 0 and visit(vertex, None) for vertex in sorted(graph.vertices))


def dead_ends(graph: Graph, finish: int) -> list[int]:
    """Find non-mandatory vertices with an arrival that requires reversing.

    For each possible incoming road, search for the finish without immediately
    traversing that same road backwards. A dead end depends on arrival direction.
    """
    if finish not in graph.vertices:
        raise ValueError("Unknown finish vertex")
    incoming = {vertex: [] for vertex in graph.vertices}
    for edge in graph.edges.values():
        if edge.status == "blocked":
            continue
        incoming[edge.target].append(edge.id)
        if not edge.directed:
            incoming[edge.source].append(edge.id)
    result = []
    for vertex_id, vertex in graph.vertices.items():
        if vertex_id == finish or vertex.kind in {"checkpoint", "start", "finish"}:
            continue
        for arrival in incoming[vertex_id]:
            queue = deque([vertex_id])
            visited = {vertex_id}
            while queue:
                current = queue.popleft()
                for neighbor, edge in graph.neighbors(current):
                    if current == vertex_id and edge.id == arrival:
                        continue
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            if finish not in visited:
                result.append(vertex_id)
                break
    return sorted(result)
