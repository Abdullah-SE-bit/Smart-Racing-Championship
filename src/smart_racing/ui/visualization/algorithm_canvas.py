"""Animated circuit telemetry driven by the Algorithm Lab's real trace."""

import math

import pygame


ICE = (111, 226, 255)
ELECTRIC = (50, 157, 255)
LIME = (166, 244, 169)
AMBER = (255, 187, 104)
PINK = (255, 102, 153)
WHITE = (243, 248, 255)
VOID = (11, 18, 27)


def _mix(first, second, amount):
    return tuple(round(a + (b - a) * amount) for a, b in zip(first, second))


def _line_glow(glow, rect, start, end, color, width=3):
    """Add restrained transparent bloom to the shared trace layer."""
    origin = pygame.Vector2(rect[:2])
    a, b = pygame.Vector2(start) - origin, pygame.Vector2(end) - origin
    pygame.draw.line(glow, (*color, 28), a, b, width + 12)
    pygame.draw.line(glow, (*color, 54), a, b, width + 6)
    pygame.draw.line(glow, (*color, 28), a, b, width + 12)
    pygame.draw.line(glow, (*color, 54), a, b, width + 6)


def _trace_vertices(trace, count, mode):
    visited = set()
    frontier = set()
    if mode == "Backtracking":
        for step in trace[:count]:
            vertex = step.get("vertex")
            if vertex is None:
                continue
            if step["action"] == "place checkpoint":
                visited.add(vertex)
            elif step["action"] == "backtrack":
                visited.discard(vertex)
            elif step["action"] == "reject placement":
                frontier.add(vertex)
    elif mode in {"BFS", "DFS"}:
        for step in trace[:count]:
            vertex = step.get("vertex")
            if vertex is None:
                continue
            if step["action"] == "visit":
                visited.add(vertex)
                frontier.discard(vertex)
            elif step["action"] == "discover":
                frontier.add(vertex)
    else:
        for step in trace[:count]:
            vertex = step.get("vertex")
            if vertex is None:
                continue
            if step["action"] == "expand":
                visited.add(vertex)
                frontier.discard(vertex)
            elif step["action"] == "relax":
                frontier.add(vertex)
    return visited, frontier


def draw_algorithm_canvas(app, rect, trace, count, mode, seconds, phase=1.0):
    """Draw trace history, current search wave and a moving pulse on its active road.

    The function is presentation-only. It reads the current circuit coordinates
    and recorded algorithm operations, and never invokes or advances an algorithm.
    """
    graph = app.circuit.graph
    positions = app.map_positions(rect, app.circuit)
    visible = trace[:max(0, min(count, len(trace)))]
    visited, frontier = _trace_vertices(trace, len(visible), mode)
    current = visible[-1] if visible else None

    palette = (ICE if mode in {"BFS", "Dijkstra", "Kruskal"}
               else PINK if mode in {"DFS", "Backtracking"}
               else ELECTRIC)
    clip = app.surface.get_clip()
    app.surface.set_clip(pygame.Rect(rect))
    glow = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)

    # Sweep the edge of the search frontier across the graph's drafting grid.
    # The slow sweep adds life to a held trace without changing its content.
    if not app.reduced_motion and visible:
        local_x = round((seconds * 54) % rect[2])
        x = rect[0] + local_x
        veil = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.line(veil, (*palette, 11), (local_x, 0), (local_x, rect[3]), 9)
        pygame.draw.line(veil, (*palette, 42), (local_x, 0), (local_x, rect[3]), 1)
        app.surface.blit(veil, (rect[0], rect[1]))

    # Draw the most recent eight edge operations as a fading telemetry trail.
    edge_steps = [(index, step) for index, step in enumerate(visible)
                  if "edge" in step and step["edge"] in graph.edges]
    recent_edges = edge_steps[-8:]
    for age, (index, step) in enumerate(recent_edges):
        edge = graph.edges[step["edge"]]
        color = _mix((45, 82, 117), palette, (age + 1) / (len(edge_steps[-8:]) + 1))
        start, end = positions[edge.source], positions[edge.target]
        _line_glow(glow, rect, start, end, color, 2 if age < len(edge_steps[-8:]) - 1 else 3)

    active_edge = None
    active_vertex = current.get("vertex") if current else None
    radius = 5
    if current and "edge" in current:
        active_edge = graph.edges.get(current["edge"])
    if active_edge:
        previous_vertex = next((step["vertex"] for step in reversed(visible[:-1]) if "vertex" in step), None)
        if active_vertex in {active_edge.source, active_edge.target} and previous_vertex in {
                active_edge.source, active_edge.target} and previous_vertex != active_vertex:
            source, target = previous_vertex, active_vertex
        else:
            source, target = active_edge.source, active_edge.target
        start, finish = positions[source], positions[target]
        _line_glow(glow, rect, start, finish, WHITE, 2)
        travel = phase
        if not app.reduced_motion:
            travel = (phase + (seconds * 1.7) % .32) % 1.0
        marker = pygame.Vector2(start).lerp(finish, travel)
        radius = 5 + round(2 * (1 + math.sin(seconds * 9))) if not app.reduced_motion else 5
        pygame.draw.circle(glow, (*palette, 50),
                           (marker.x - rect[0], marker.y - rect[1]), radius + 8)

    # Give vertices semantic states rather than coloring every visited node alike.
    for vertex_id in visited:
        point = positions[vertex_id]
        pygame.draw.circle(glow, (*LIME, 36), (point[0] - rect[0], point[1] - rect[1]), 12)
        pygame.draw.circle(app.surface, LIME, point, 4, 1)
    for vertex_id in frontier:
        point = positions[vertex_id]
        pygame.draw.circle(glow, (*palette, 36), (point[0] - rect[0], point[1] - rect[1]), 12)
        pygame.draw.circle(app.surface, palette, point, 5, 1)

    if active_vertex in positions:
        x, y = positions[active_vertex]
        if app.reduced_motion:
            pulse = 1.0
        else:
            pulse = (1 + math.sin(seconds * 7)) / 2
        radius = 11 + round(5 * pulse)
        pygame.draw.circle(glow, (*palette, 38), (x - rect[0], y - rect[1]), radius + 7)
    app.surface.blit(glow, rect[:2])

    for age, (_, step) in enumerate(recent_edges):
        edge = graph.edges[step["edge"]]
        color = _mix((45, 82, 117), palette, (age + 1) / (len(recent_edges) + 1))
        pygame.draw.aaline(app.surface, color, positions[edge.source], positions[edge.target])
        if age == len(recent_edges) - 1:
            pygame.draw.line(app.surface, color, positions[edge.source], positions[edge.target], 2)
    if active_edge:
        pygame.draw.aaline(app.surface, WHITE, start, finish)
        pygame.draw.line(app.surface, WHITE, start, finish, 2)
        pygame.draw.circle(app.surface, WHITE, marker, 5)
        pygame.draw.circle(app.surface, palette, marker, 3)
    for vertex_id in visited:
        pygame.draw.circle(app.surface, LIME, positions[vertex_id], 4, 1)
    for vertex_id in frontier:
        pygame.draw.circle(app.surface, palette, positions[vertex_id], 5, 1)
    if active_vertex in positions:
        pygame.draw.circle(app.surface, palette, positions[active_vertex], radius, 2)
        pygame.draw.circle(app.surface, WHITE, positions[active_vertex], 3)

    # A small sweep across the footer gives a live telemetry readout.
    if not app.reduced_motion and visible:
        sweep_x = rect[0] + round((seconds * 150) % rect[2])
        pygame.draw.line(app.surface, (*palette, 115), (sweep_x, rect[1] + rect[3] - 2),
                         (min(sweep_x + 18, rect[0] + rect[2]), rect[1] + rect[3] - 2), 2)
    app.surface.set_clip(clip)
