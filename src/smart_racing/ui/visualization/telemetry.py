"""Circuit drafting surface and instrument views for real algorithm traces."""

from functools import lru_cache

import pygame

from smart_racing.championship.standings import ranking_key
from smart_racing.ui.visualization.algorithm_canvas import draw_algorithm_canvas


INK = (14, 21, 28)
GRID = (31, 42, 51)
SILVER = (183, 196, 207)
WHITE = (244, 245, 248)
BLUE = (115, 196, 239)
RED = (255, 102, 100)


@lru_cache(maxsize=12)
def drafting_surface(width, height):
    panel = pygame.Surface((width, height))
    panel.fill(INK)
    for x in range(16, width, 32):
        for y in range(16, height, 32):
            panel.set_at((x, y), (52, 65, 76))
    for x in range(16, width, 128):
        pygame.draw.line(panel, GRID, (x, 0), (x, height))
    for y in range(16, height, 128):
        pygame.draw.line(panel, GRID, (0, y), (width, y))
    for x, dx in ((0, 1), (width - 1, -1)):
        for y, dy in ((0, 1), (height - 1, -1)):
            pygame.draw.lines(panel, SILVER, False, [(x + dx * 12, y), (x, y), (x, y + dy * 12)])
    return panel


def _operation_name(action):
    return {
        "heap insert": "INSERT INTO PRIORITY QUEUE",
        "heap extract": "EXTRACT HIGHEST PRIORITY",
        "heapify": "BUILD PRIORITY QUEUE",
        "merge": "MERGE ORDERED RUNS",
        "partition": "PARTITION AROUND PIVOT",
        "extract maximum": "PLACE MAXIMUM IN SORTED SUFFIX",
        "dp row": "UPDATE KNAPSACK ROW",
        "consider pickup": "EVALUATE PICKUP",
    }.get(action, action.replace("_", " ").upper())


def _transition_phase(app):
    if app.reduced_motion or not app.lab_playing:
        return 1
    fraction = (app.lab_step % 1) * 2
    fraction = min(1, fraction)
    return 1 - (1 - fraction) ** 3


def _glow(surface, center, color, radius, alpha=45):
    haze = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
    for ring in range(3, 0, -1):
        pygame.draw.circle(haze, (*color, alpha // (ring + 1)), (radius * 2, radius * 2),
                           radius + ring * radius // 2)
    surface.blit(haze, (round(center[0] - radius * 2), round(center[1] - radius * 2)))


def _scanline(app, board):
    if app.reduced_motion:
        return
    x = board[0] + 12 + (app.time * 105) % (board[2] - 24)
    tint = pygame.Surface((15, board[3] - 4), pygame.SRCALPHA)
    tint.fill((115, 196, 239, 13))
    app.surface.blit(tint, (round(x), board[1] + 2))


def _center(app, text, x, y, size, color):
    width = app.fonts[size].size(text)[0]
    app.label(text, x - width / 2, y, size, color)


def endpoint_flag(app, xy, title, color, above=True):
    """Offset the flag from its hit target so the vertex stays selectable."""
    x, y = xy
    width = app.fonts[14].size(title)[0] + 12
    rect = pygame.Rect(x - width // 2, y - 34 if above else y + 13, width, 21)
    pygame.draw.line(app.surface, color, xy, (x, rect.bottom if above else rect.top))
    pygame.draw.rect(app.surface, INK, rect)
    pygame.draw.rect(app.surface, color, rect, 1)
    _center(app, title, x, rect.y + 1, 14, WHITE)


def route_thumbnail(surface, rect, circuit, route):
    vertices = circuit.graph.vertices
    xs = [v.x for v in vertices.values()]
    ys = [v.y for v in vertices.values()]
    scale = min((rect.width - 8) / max(1, max(xs) - min(xs)),
                (rect.height - 8) / max(1, max(ys) - min(ys)))
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    points = {i: (rect.centerx + (v.x - cx) * scale, rect.centery + (v.y - cy) * scale)
              for i, v in vertices.items()}
    for edge in circuit.graph.edges.values():
        pygame.draw.aaline(surface, (76, 85, 97), points[edge.source], points[edge.target])
    if len(route.vertices) > 1:
        line = [points[i] for i in route.vertices]
        pygame.draw.lines(surface, BLUE, False, line, 2)
        pygame.draw.circle(surface, WHITE, line[0], 3)
        pygame.draw.circle(surface, RED, line[-1], 3)


def _rank_label(key, entries):
    if isinstance(key, tuple):
        return next((entry.name for entry in entries if entry.racer_id == key[-1]), str(key[-1]))
    return str(key)


def _heap_positions(count):
    positions = []
    for index in range(count):
        level = (index + 1).bit_length() - 1
        slots = 2 ** level
        column = index - slots + 1
        positions.append((round(80 + (column + .5) * 720 / slots), 348 + level * 69))
    return positions


def _heap(app, current, previous, phase):
    keys = current.get("keys", [])
    is_event = app.lab_algorithm == "Event heap"
    app.label("ROAD PRIORITY QUEUE" if is_event else "TOP-K CANDIDATES", 88, 260, 20, WHITE)
    caption = "Node label = road time in seconds   /   ties use difficulty, then sequence" if is_event else "The lowest-ranked retained candidate is at the root"
    app.label(caption, 88, 294, 14, SILVER)
    if not keys:
        _center(app, "EMPTY HEAP", 440, 430, 20, SILVER)
        return
    positions = _heap_positions(len(keys))
    previous_keys = previous.get("keys", ())
    origins = dict(zip(previous_keys, _heap_positions(len(previous_keys))))
    target_positions = _heap_positions(len(keys))
    prior_set = set(previous_keys)
    for index, key in enumerate(keys):
        x, y = target_positions[index]
        old_x, old_y = origins.get(key, (x, y - 18))
        positions[index] = (round(old_x + (x - old_x) * phase), round(old_y + (y - old_y) * phase))
        if not app.reduced_motion and (key not in prior_set or origins.get(key) != target_positions[index]):
            _glow(app.surface, positions[index], RED if index == 0 else BLUE, 8,
                  round(40 * (1 - phase) + 18))
    for index in range(1, len(keys)):
        pygame.draw.line(app.surface, (86, 113, 132), positions[(index - 1) // 2], positions[index], 2)
    for index, (key, (x, y)) in enumerate(zip(keys, positions)):
        color = RED if index == 0 else BLUE
        value = f"{key[0]:g}" if is_event else _rank_label(key, app.entries)
        width = max(60, app.fonts[18].size(value)[0] + 16)
        box = pygame.Rect(0, 0, width, 34)
        box.center = x, y
        pygame.draw.rect(app.surface, (29, 40, 49), box, border_radius=5)
        pygame.draw.rect(app.surface, color, box, 2, border_radius=5)
        _center(app, value, x, y - 12, 18, WHITE)


def _columns(app, labels, amounts, marked, unit, origins=None, phase=1, previous_amounts=None):
    # Zero has a baseline marker and a printed value, so it remains distinct
    # from a missing reading. All bars in this panel use the same units.
    left, right, bottom = 90, 786, 542
    maximum = max(1, max(amounts, default=0))
    previous_amounts = previous_amounts or {}
    slot = (right - left) / len(amounts)
    for index, (label, amount) in enumerate(zip(labels, amounts)):
        x = left + (index + .5) * slot
        if origins:
            old_x = origins.get(label, x)
            x = old_x + (x - old_x) * phase
        width = min(56, max(4, slot - 8))
        old_amount = previous_amounts.get(label, amount)
        animated_amount = old_amount + (amount - old_amount) * phase
        height = round(154 * animated_amount / maximum)
        color = RED if index in marked else BLUE
        rect = pygame.Rect(round(x - width / 2), bottom - max(2, height), round(width), max(2, height))
        pygame.draw.rect(app.surface, color, rect, border_top_left_radius=3, border_top_right_radius=3)
        if index in marked and not app.reduced_motion:
            _glow(app.surface, (x, rect.top + 5), color, 7, 34)
        _center(app, str(amount), x, rect.top - 26, 16, WHITE)
        _center(app, label, x, bottom + 7, 14, SILVER)
    pygame.draw.line(app.surface, SILVER, (left, bottom), (right, bottom))
    app.label(unit, 90, 584, 14, SILVER)


def _sorting(app, current, previous, phase):
    keys = current.get("values")
    if keys is None:
        keys = list(reversed(app.circuit.checkpoints))
        if app.entries:
            keys = [ranking_key(entry) for entry in reversed(app.entries)]
    action = current.get("action", "input order")
    app.label(_operation_name(action), 88, 260, 20, WHITE)
    app.label("Current segment in execution order", 88, 297, 16, SILVER)
    labels = [_rank_label(key, app.entries) for key in keys]
    amounts = [-key[0] if isinstance(key, tuple) else key for key in keys]
    # Circuit vertex IDs may be negative; show their relative rank instead
    # of treating an identifier as a physical quantity.
    if not app.entries:
        ranks = {vertex: rank for rank, vertex in enumerate(sorted(app.circuit.checkpoints), 1)}
        amounts = [ranks[key] for key in keys]
    marked = {i for i, key in enumerate(keys)
              if key == current.get("pivot") or i >= current.get("sorted_from", len(keys))}
    unit = "Height = championship points" if app.entries else "Height = checkpoint ID rank"
    previous_keys = previous.get("values", [])
    origins = {_rank_label(key, app.entries): 90 + (index + .5) * 696 / len(previous_keys)
               for index, key in enumerate(previous_keys)}
    if app.entries:
        previous_amounts = {_rank_label(key, app.entries): -key[0] for key in previous_keys}
    else:
        ranks = {vertex: rank for rank, vertex in enumerate(sorted(app.circuit.checkpoints), 1)}
        previous_amounts = {str(key): ranks[key] for key in previous_keys}
    _columns(app, labels, amounts, marked, unit, origins, phase, previous_amounts)


def _resources(app, current, previous, has_trace, phase):
    dp = app.lab_algorithm == "Knapsack"
    app.label("BUDGET TABLE" if dp else "PICKUP DECISION", 88, 260, 20, WHITE)
    if not has_trace:
        app.label("No feasible pickup between these endpoints.", 88, 350, 18, SILVER)
        return
    if dp:
        values = current.get("capacities", [0] * 11)
        title = f"Best benefit after considering pickup {current['item']}" if current else "Base row before considering pickups"
        app.label(title, 88, 295, 16, SILVER)
        old = previous.get("capacities", [0] * len(values)) if previous else [0] * len(values)
        _columns(app, [str(i) for i in range(len(values))], values,
                 {i for i, (a, b) in enumerate(zip(old, values)) if a != b},
                 "Detour budget by column", phase=phase,
                 previous_amounts={str(i): value for i, value in enumerate(old)})
        pygame.draw.rect(app.surface, RED, (90, 535, 696, 3))
        if not app.reduced_motion:
            runner = 90 + round(696 * ((app.time * 1.4) % 1))
            _glow(app.surface, (runner, 536), RED, 5, 38)
        return
    if not current:
        app.label("Step forward to consider the first pickup.", 88, 350, 18, SILVER)
        return
    app.label(f"Pickup {current['item']}   /   {'SELECTED' if current['selected'] else 'SKIPPED'}",
              88, 325, 30, WHITE)
    _columns(app, ["Spent", "Remaining"], [current["cost"], current["budget"] - current["cost"]],
             {0} if current["selected"] else set(),
             f"Detour budget units    /    benefit earned {current['value']}")


def draw_trace_board(app, trace, count):
    """Read the selected execution prefix. Drawing never changes the trace."""
    board = (60, 242, 760, 375)
    current = trace[count - 1] if count else {}
    previous = trace[count - 2] if count > 1 else {}
    phase = app.lab_animation_phase() if hasattr(app, "lab_animation_phase") else _transition_phase(app)
    mode = app.lab_algorithm
    if mode in {"Event heap", "Top-k", "Merge sort", "Quick sort", "Heap sort", "Knapsack", "Greedy"}:
        app.surface.blit(drafting_surface(*board[2:]), board[:2])
        _scanline(app, board)
        if current:
            app.label(_operation_name(current.get("action", "")), 88, 606, 14, RED)
    if mode in {"Event heap", "Top-k"}:
        _heap(app, current, previous, phase)
    elif mode in {"Merge sort", "Quick sort", "Heap sort"}:
        _sorting(app, current, previous, phase)
    elif mode in {"Knapsack", "Greedy"}:
        _resources(app, current, previous, bool(trace), phase)
    else:
        steps = trace[:count]
        visited = set()
        for step in steps:
            if (mode != "Backtracking" and "vertex" in step) or step["action"] == "place checkpoint":
                visited.add(step["vertex"])
            elif step["action"] == "backtrack":
                visited.discard(step["vertex"])
        roads = [step["edge"] for step in steps if "edge" in step]
        app.draw_map(board, app.circuit, roads, visited)
        draw_algorithm_canvas(app, board, trace, count, mode, app.time, phase)
