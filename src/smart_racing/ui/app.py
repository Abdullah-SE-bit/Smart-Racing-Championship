"""Pygame presentation; race rules and algorithms stay in their own modules."""

import math
import sys
from copy import deepcopy
from pathlib import Path

import pygame

from smart_racing.algorithms.graph.traversal import bfs, bounded_simple_paths, dead_ends, dfs, has_cycle, weak_components
from smart_racing.algorithms.generation.mst import kruskal
from smart_racing.algorithms.optimization.resources import Pickup, greedy, knapsack
from smart_racing.algorithms.routing.shortest import checkpoint_route, shortest_path
from smart_racing.algorithms.sorting.rankings import heap_sort, merge_sort, quick_sort, top_k
from smart_racing.algorithms.structures.heap import MinHeap
from smart_racing.championship.standings import ChampionshipEntry, award_results, leaders, ranking_key, standings
from smart_racing.core.graph import CostProfile, Graph
from smart_racing.events.queue import Event
from smart_racing.game.race import Race
from smart_racing.game.clock import SimulationClock
from smart_racing.resources.planner import pickup_suggestions, route_refuelling
from smart_racing.tracks.circuits import load_circuit, save_circuit, validate_circuit
from smart_racing.tracks.generator import _assign_checkpoints, _ring_compatible, generate_circuit


WIDTH, HEIGHT = 1280, 800
PLANNER_MAP = (60, 242, 760, 400)
BACKGROUND = (17, 31, 27)
PANEL = (28, 44, 37)
PANEL_LIGHT = (40, 57, 47)
TEXT = (246, 239, 220)
MUTED = (174, 185, 167)
ACCENT = (215, 224, 128)
GOLD = (237, 139, 91)
PINK = (232, 159, 145)
CAR_COLORS = (ACCENT, GOLD, PINK, (151, 183, 192))
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
PROFILES = {
    "Balanced": CostProfile(),
    "Speed": CostProfile(distance=.2, time=3, fuel=.2, difficulty=.2, obstacle=.3),
    "Economy": CostProfile(distance=.3, time=.2, fuel=3, difficulty=.3, obstacle=.2),
    "Safety": CostProfile(distance=.3, time=.3, fuel=.3, difficulty=3, obstacle=3),
}
LAB_ALGORITHMS = ["BFS", "DFS", "Dijkstra", "Astar", "Knapsack", "Greedy", "Backtracking",
                  "Kruskal", "Event heap", "Merge sort", "Quick sort", "Heap sort", "Top-k"]


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Smart Racing Championship")
        self.window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.surface = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = {size: pygame.font.SysFont("segoeui", size, bold=bold)
                      for size, bold in [(14, False), (16, False), (18, False), (20, True),
                                         (24, True), (30, True), (42, True), (62, True)]}
        self.authored_paths = sorted((ROOT / "data" / "circuits").glob("*.json"))
        self.saved_directory = Path.home() / "SmartRacingChampionship" / "circuits"
        self.circuit_paths = self.authored_paths + sorted(self.saved_directory.glob("*.json"))
        self.track_index = 0
        self.circuit = load_circuit(self.circuit_paths[0])
        self.screen = "menu"
        self.running = True
        self.time = 0.0
        self.reduced_motion = False
        self.transition_remaining = 0.0
        self.previous_frame = None
        self.simulation_clock = SimulationClock()
        self.buttons = []
        self.focused_button = 0
        self.keyboard_focus = False
        self.race = None
        self.selected_road = 0
        self.championship = False
        self.pending_championship = False
        self.entries = []
        self.recorded = False
        self.profile_index = 0
        self.route_algorithm = "dijkstra"
        self.source = self.circuit.start
        self.target = self.circuit.checkpoints[min(3, len(self.circuit.checkpoints) - 1)]
        self.ordered_plan = False
        self.lab_algorithm = "BFS"
        self.lab_step = 0.0
        self.lab_playing = True
        self.lab_speed = 3.0
        self.paused = False
        self.laps_setting = 2
        self.limit_setting = 240
        self.top_k_count = 3
        self.sort_method = "Merge"
        self.validation_message = ""
        self._refuel_cache = {}
        self._pickup_cache = {}
        self.refuel_page = 0
        self.alternative_paths = []
        self.alternative_index = 0
        self.alternative_truncated = False
        self.generation_trace = []
        self.generation_started = 0.0

    def label(self, text, x, y, size=18, color=TEXT):
        self.surface.blit(self.fonts[size].render(str(text), True, color), (int(x), int(y)))

    def card(self, rect, color=PANEL, radius=18, border=(63, 82, 67)):
        pygame.draw.rect(self.surface, color, rect, border_radius=radius)
        pygame.draw.rect(self.surface, border, rect, width=1, border_radius=radius)

    def button(self, rect, title, action, selected=False, subtitle=None):
        rect = pygame.Rect(rect)
        hover = rect.collidepoint(self.logical_position(pygame.mouse.get_pos()))
        color = (67, 78, 52) if selected else ((56, 75, 61) if hover else PANEL_LIGHT)
        self.card(rect, color, 12, ACCENT if selected else (70, 89, 72))
        if self.keyboard_focus and self.focused_button == len(self.buttons):
            pygame.draw.rect(self.surface, GOLD, rect, width=2, border_radius=12)
        self.label(title, rect.x + 15, rect.y + (8 if subtitle else 11), 18, ACCENT if selected else TEXT)
        if subtitle:
            self.label(subtitle, rect.x + 15, rect.y + 34, 14, MUTED)
        self.buttons.append((rect, action))

    def background(self):
        self.surface.fill(BACKGROUND)
        for index in range(16):
            x = int((index * 131 + (0 if self.reduced_motion else self.time * 11)) % (WIDTH + 100)) - 50
            pygame.draw.line(self.surface, (25, 43, 35), (x, 0), (x - 220, HEIGHT), 1)
        pygame.draw.rect(self.surface, (20, 36, 30), (0, 0, WIDTH, 70))
        pygame.draw.polygon(self.surface, ACCENT, [(39, 22), (49, 34), (39, 46), (29, 34)], 2)
        self.label("PADDOCK", 65, 17, 24)
        self.label("/ SMART RACING CHAMPIONSHIP", 195, 23, 14, MUTED)
        self.label("DAA  •  RACE LAB", 1078, 24, 14, ACCENT)
        pygame.draw.line(self.surface, (61, 78, 63), (0, 69), (WIDTH, 69))

    def header(self, eyebrow, title, description):
        self.label(eyebrow.upper(), 48, 92, 14, ACCENT)
        self.label(title, 45, 111, 42)
        self.label(description, 48, 170, 16, MUTED)

    def nav(self):
        self.button((1045, 91, 185, 44), "←  Main menu", lambda: self.go("menu"))

    def go(self, screen):
        if screen != self.screen and not self.reduced_motion:
            self.previous_frame = self.surface.copy()
            self.transition_remaining = .22
        else:
            self.transition_remaining = 0
        if screen != self.screen:
            self.buttons = []
            self.focused_button = 0
        self.screen = screen
        self.lab_step = 0

    def viewport(self):
        width, height = self.window.get_size()
        scale = min(max(width, 1) / WIDTH, max(height, 1) / HEIGHT)
        viewport_width = max(1, round(WIDTH * scale))
        viewport_height = max(1, round(HEIGHT * scale))
        return ((width - viewport_width) // 2, (height - viewport_height) // 2,
                viewport_width, viewport_height)

    def logical_position(self, position):
        left, top, width, height = self.viewport()
        return ((position[0] - left) * WIDTH / width,
                (position[1] - top) * HEIGHT / height)

    def present(self):
        left, top, width, height = self.viewport()
        self.window.fill(BACKGROUND)
        frame = self.surface if (width, height) == (WIDTH, HEIGHT) else pygame.transform.smoothscale(
            self.surface, (width, height))
        self.window.blit(frame, (left, top))
        pygame.display.flip()

    def set_track(self, direction):
        self.track_index = (self.track_index + direction) % len(self.circuit_paths)
        self.circuit = load_circuit(self.circuit_paths[self.track_index])
        self._refuel_cache.clear()
        self.validation_message = ""
        self.source = self.circuit.start
        self.target = self.circuit.checkpoints[min(3, len(self.circuit.checkpoints) - 1)]

    def start_race(self, championship=False, next_race=False):
        if championship and not next_race:
            self.track_index = 0
            self.circuit = load_circuit(self.circuit_paths[0])
            self.entries = [ChampionshipEntry(i, name) for i, name in enumerate(("YOU", "NOVA", "BLAZE", "VECTOR"))]
        self.championship = championship
        self.pending_championship = False
        self.race = Race(deepcopy(self.circuit), laps_required=self.laps_setting,
                         time_limit=self.limit_setting)
        graph = self.race.circuit.graph
        if len(graph.edges) > 8:
            # Circuit IDs are stable identifiers, not indexes into a sequence.
            # Selecting from sorted actual IDs keeps the demo deterministic for
            # authored, generated, and user-saved tracks alike.
            roads = sorted(graph.edges)
            shortcut = min(edge.id for edge in graph.edges.values() if edge.shortcut)
            fuel = min(vertex.id for vertex in graph.vertices.values() if vertex.kind == "fuel")
            nitro = min(vertex.id for vertex in graph.vertices.values() if vertex.kind == "nitro")
            self.race.schedule(Event(0, 12, 1, "block", roads[8], 9))
            self.race.schedule(Event(1, 24, 4, "restriction", roads[5], 12))
            self.race.schedule(Event(2, 7, 3, "oil", roads[4], 20))
            self.race.schedule(Event(3, 10, 2, "shortcut_close", shortcut))
            self.race.schedule(Event(4, 18, 2, "shortcut_open", shortcut))
            self.race.schedule(Event(5, 20, 5, "fuel_off", fuel, 30))
            self.race.schedule(Event(6, 22, 6, "nitro_on", nitro, 25))
        self.selected_road = 0
        self.simulation_clock = SimulationClock()
        self.recorded = False
        self.paused = False
        self.go("race")

    def next_championship_race(self):
        if self.track_index + 1 < len(self.authored_paths):
            self.set_track(1)
            self.pending_championship = True
            self.go("planner")
        else:
            self.pending_championship = False
            self.go("menu")

    def prepare_championship(self):
        """Begin a new championship at the first circuit's planning screen."""
        self.track_index = 0
        self.circuit = load_circuit(self.authored_paths[0])
        self.source = self.circuit.start
        self.target = self.circuit.checkpoints[min(3, len(self.circuit.checkpoints) - 1)]
        self._refuel_cache.clear()
        self.validation_message = ""
        self.entries = [ChampionshipEntry(i, name) for i, name in enumerate(("YOU", "NOVA", "BLAZE", "VECTOR"))]
        self.pending_championship = True
        self.go("planner")

    def open_quick_planner(self):
        self.pending_championship = False
        self.go("planner")

    def start_planned_race(self):
        if self.pending_championship:
            self.start_race(championship=True, next_race=True)
        else:
            self.start_race(championship=False)

    def menu_button(self, rect, title, detail, action, primary=False):
        """Draw a large menu action using the same input and focus system."""
        rect = pygame.Rect(rect)
        hover = rect.collidepoint(self.logical_position(pygame.mouse.get_pos()))
        focused = self.keyboard_focus and self.focused_button == len(self.buttons)
        fill = (242, 103, 64) if primary else (34, 42, 44) if hover else (26, 32, 34)
        border = (255, 187, 145) if focused else (255, 132, 92) if primary else (65, 76, 75)
        pygame.draw.rect(self.surface, fill, rect, border_radius=8)
        pygame.draw.rect(self.surface, border, rect, 2 if focused else 1, border_radius=8)
        ink = (27, 28, 26) if primary else (244, 239, 225)
        if rect.width <= 60:
            self.label(title, rect.centerx - 5, rect.y + 9, 20, ink)
        else:
            self.label(title, rect.x + 18, rect.y + 9, 18 if rect.width < 250 else 20, ink)
        if detail:
            self.label(detail, rect.x + 18, rect.y + 35, 14,
                       (79, 43, 32) if primary else (159, 171, 164))
        if rect.width >= 250:
            self.label("›", rect.right - 28, rect.centery - 14, 24, ink)
        self.buttons.append((rect, action))

    def draw_menu_circuit(self, rect):
        """Draw a stylized preview from the selected circuit's actual roads."""
        positions = self.map_positions(rect, self.circuit)
        graph = self.circuit.graph
        route = [positions[vertex] for vertex in self.circuit.main_route]
        # Secondary roads are deliberately quieter than the main circuit.
        for edge in graph.edges.values():
            a, b = positions[edge.source], positions[edge.target]
            pygame.draw.line(self.surface, (49, 65, 64), a, b, 8)
            pygame.draw.line(self.surface, (84, 100, 94) if edge.shortcut else (36, 49, 48), a, b, 3)
        if len(route) < 2:
            return
        # Layered roads and rounded junctions evoke a physical circuit while
        # preserving the topology of the stored main route.
        for width, color in ((30, (17, 26, 26)), (25, (209, 110, 76)),
                             (20, (56, 68, 67)), (15, (42, 52, 52))):
            pygame.draw.lines(self.surface, color, False, route, width)
            for point in route:
                pygame.draw.circle(self.surface, color, point, width // 2)
        for a, b in zip(route, route[1:]):
            length = math.dist(a, b)
            if not length:
                continue
            for offset in range(0, int(length), 25):
                start = offset / length
                end = min(offset + 10, length) / length
                pygame.draw.line(self.surface, (132, 145, 133),
                                 (a[0] + (b[0] - a[0]) * start, a[1] + (b[1] - a[1]) * start),
                                 (a[0] + (b[0] - a[0]) * end, a[1] + (b[1] - a[1]) * end), 1)
        start = positions[self.circuit.start]
        pygame.draw.circle(self.surface, (244, 239, 225), start, 6)
        pygame.draw.circle(self.surface, (20, 29, 28), start, 3)
        # The preview is decorative: moving markers do not affect race state.
        lengths = [math.dist(a, b) for a, b in zip(route, route[1:])]
        total = sum(lengths)
        if total:
            for index, color in enumerate(((247, 111, 66), (232, 226, 201), (127, 177, 158))):
                distance = ((0 if self.reduced_motion else self.time * 38) + index * total / 3) % total
                for segment, length in enumerate(lengths):
                    if distance <= length and length:
                        a, b = route[segment], route[segment + 1]
                        t = distance / length
                        point = (round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t))
                        pygame.draw.circle(self.surface, (12, 20, 19), point, 8)
                        pygame.draw.circle(self.surface, color, point, 5)
                        break
                    distance -= length

    def draw_pit_background(self):
        self.surface.fill((13, 20, 20))
        pygame.draw.rect(self.surface, (18, 27, 26), (0, 0, WIDTH, 70))
        pygame.draw.line(self.surface, (53, 65, 61), (0, 69), (WIDTH, 69))
        pygame.draw.polygon(self.surface, (244, 103, 64), [(48, 22), (59, 34), (48, 46), (37, 34)])
        self.label("PADDOCK", 72, 18, 24, (247, 242, 228))
        self.label("SMART RACING CHAMPIONSHIP", 218, 25, 14, (140, 155, 145))
        self.label("SEASON 01   /   RACE CONTROL", 1018, 25, 14, (159, 171, 160))

    def draw_menu(self):
        self.draw_pit_background()
        self.label("THE GRID IS READY", 48, 108, 14, (246, 125, 84))
        self.label("OWN THE", 44, 137, 62, (248, 244, 231))
        self.label("RACING LINE.", 44, 205, 42, (246, 125, 84))
        self.label("Choose your route. Make every move count.", 48, 268, 18, (170, 182, 172))
        self.menu_button((48, 319, 420, 65), "CHAMPIONSHIP", "Three circuits  /  one champion", self.prepare_championship, True)
        self.menu_button((48, 396, 420, 65), "QUICK RACE", "Head straight to the starting grid", lambda: self.start_race(False))
        self.menu_button((48, 473, 204, 50), "ROUTE PLANNER", None, self.open_quick_planner)
        self.menu_button((264, 473, 204, 50), "ALGORITHM LAB", None, lambda: self.go("lab"))
        self.menu_button((48, 535, 420, 50), "CONTROLS & SETTINGS", None, lambda: self.go("settings"))
        self.label("SELECT CIRCUIT", 48, 623, 14, (153, 168, 158))
        self.menu_button((48, 654, 58, 50), "‹", None, lambda: self.set_track(-1))
        self.menu_button((410, 654, 58, 50), "›", None, lambda: self.set_track(1))
        self.label(f"{self.track_index + 1:02} / {len(self.circuit_paths):02}", 122, 660, 14, (246, 125, 84))
        name = self.circuit.name.upper()
        while self.fonts[20].size(name)[0] > 260 and len(name) > 1:
            name = name[:-1]
        self.label(name, 122, 679, 20, (247, 242, 228))

        pygame.draw.rect(self.surface, (21, 33, 32), (510, 100, 722, 625), border_radius=12)
        pygame.draw.rect(self.surface, (58, 73, 68), (510, 100, 722, 625), 1, border_radius=12)
        self.label("FEATURED CIRCUIT", 540, 126, 14, (246, 125, 84))
        preview_name = self.circuit.name.upper()
        while self.fonts[30].size(preview_name)[0] > 650 and len(preview_name) > 1:
            preview_name = preview_name[:-1]
        self.label(preview_name, 538, 150, 30, (247, 242, 228))
        self.label("TRACK PREVIEW", 1086, 130, 14, (146, 165, 154))
        self.draw_menu_circuit((550, 204, 645, 405))
        pygame.draw.line(self.surface, (59, 74, 69), (540, 629), (1202, 629))
        self.label(f"{len(self.circuit.checkpoints):02}", 540, 651, 24, (247, 242, 228))
        self.label("CHECKPOINTS", 540, 682, 14, (153, 168, 158))
        self.label(f"{sum(edge.shortcut for edge in self.circuit.graph.edges.values()):02}", 750, 651, 24, (247, 242, 228))
        self.label("SHORTCUTS", 750, 682, 14, (153, 168, 158))
        self.label("04", 945, 651, 24, (247, 242, 228))
        self.label("RACERS", 945, 682, 14, (153, 168, 158))

    def map_positions(self, rect, circuit):
        left, top, width, height = rect
        points = circuit.graph.vertices.values()
        min_x, max_x = min(v.x for v in points), max(v.x for v in points)
        min_y, max_y = min(v.y for v in points), max(v.y for v in points)
        scale = min((width - 70) / max(1, max_x - min_x), (height - 70) / max(1, max_y - min_y))
        cx, cy = (min_x + max_x) / 2, (min_y + max_y) / 2
        return {v.id: (int(left + width / 2 + (v.x - cx) * scale),
                       int(top + height / 2 + (v.y - cy) * scale)) for v in points}

    def draw_map(self, rect, circuit, route=None, visited=(), racers=(), selected_edge=None, unreachable=(),
                 service_active=None, race_style=False):
        positions = self.map_positions(rect, circuit)
        selected = set(route or [])
        for edge in circuit.graph.edges.values():
            a, b = positions[edge.source], positions[edge.target]
            color = (97, 53, 47) if edge.status == "blocked" else ((93, 77, 47) if edge.status == "restricted" else (75, 93, 77))
            pygame.draw.line(self.surface, (15, 28, 23), a, b, 20 if race_style else 13)
            pygame.draw.line(self.surface, color, a, b, 15 if race_style else 8)
            if race_style and edge.status == "open":
                pygame.draw.line(self.surface, (42, 54, 52), a, b, 10)
            if edge.id == selected_edge:
                pulse = 0 if self.reduced_motion else int((1 + math.sin(self.time * 5)) / 2 * 2)
                pygame.draw.line(self.surface, GOLD, a, b, 6 + pulse)
            elif edge.id in selected:
                pygame.draw.line(self.surface, ACCENT, a, b, 5)
            elif edge.shortcut:
                pygame.draw.line(self.surface, (188, 142, 89), a, b, 3)
            middle = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
            if edge.directed and a != b:
                angle = math.atan2(b[1] - a[1], b[0] - a[0])
                forward = (math.cos(angle), math.sin(angle))
                side = (-forward[1], forward[0])
                tip = (middle[0] + 6 * forward[0], middle[1] + 6 * forward[1])
                left = (middle[0] - 5 * forward[0] + 4 * side[0], middle[1] - 5 * forward[1] + 4 * side[1])
                right = (middle[0] - 5 * forward[0] - 4 * side[0], middle[1] - 5 * forward[1] - 4 * side[1])
                pygame.draw.polygon(self.surface, TEXT, (tip, left, right))
            if edge.obstacle:
                pygame.draw.polygon(self.surface, GOLD, [(middle[0], middle[1] - 6),
                                                         (middle[0] + 6, middle[1]),
                                                         (middle[0], middle[1] + 6),
                                                         (middle[0] - 6, middle[1])])
            if edge.status == "blocked":
                pygame.draw.line(self.surface, PINK, (middle[0] - 6, middle[1] - 6),
                                 (middle[0] + 6, middle[1] + 6), 3)
                pygame.draw.line(self.surface, PINK, (middle[0] + 6, middle[1] - 6),
                                 (middle[0] - 6, middle[1] + 6), 3)
        for vertex in circuit.graph.vertices.values():
            x, y = positions[vertex.id]
            color = GOLD if vertex.kind == "fuel" else PINK if vertex.kind == "nitro" else ACCENT if vertex.id in visited else MUTED
            radius = 7 if vertex.kind in {"start", "checkpoint"} else 6
            pygame.draw.circle(self.surface, BACKGROUND, (x, y), radius + 4)
            pygame.draw.circle(self.surface, color, (x, y), radius, 2 if vertex.id not in visited else 0)
            if vertex.id in unreachable:
                pygame.draw.line(self.surface, PINK, (x - 6, y - 6), (x + 6, y + 6), 2)
                pygame.draw.line(self.surface, PINK, (x + 6, y - 6), (x - 6, y + 6), 2)
            if service_active is not None and vertex.kind in {"fuel", "nitro"} and not service_active[vertex.id]:
                pygame.draw.line(self.surface, PINK, (x - 8, y + 8), (x + 8, y - 8), 2)
            if vertex.kind == "checkpoint":
                self.label(str(vertex.checkpoint_order), x + 9, y - 15, 14, TEXT)
            elif vertex.kind in {"fuel", "nitro"}:
                self.label(f"{'F' if vertex.kind == 'fuel' else 'N'}{vertex.id}", x + 9, y - 15, 14, color)
        for racer in racers:
            x, y = positions[racer.vertex]
            heading = -math.pi / 2
            if racer.edge_id is not None:
                tx, ty = positions[racer.edge_target]
                heading = math.atan2(ty - y, tx - x)
                x += (tx - x) * racer.edge_progress
                y += (ty - y) * racer.edge_progress
            x += (racer.id % 2) * 7 - 3
            y += (racer.id // 2) * 7 - 3
            forward = (math.cos(heading), math.sin(heading))
            side = (-forward[1], forward[0])
            if race_style:
                def car_point(along, across):
                    return (round(x + along * forward[0] + across * side[0]),
                            round(y + along * forward[1] + across * side[1]))

                # A small top-down car stays attached to the real interpolated
                # racer position; decoration does not change simulation state.
                body = [car_point(9, 0), car_point(6, 5), car_point(-7, 5),
                        car_point(-9, 3), car_point(-9, -3), car_point(-7, -5), car_point(6, -5)]
                pygame.draw.polygon(self.surface, (9, 16, 15), body, 4)
                pygame.draw.polygon(self.surface, CAR_COLORS[racer.id % len(CAR_COLORS)], body)
                pygame.draw.polygon(self.surface, (28, 38, 37),
                                    [car_point(3, 3), car_point(-3, 3), car_point(-3, -3), car_point(3, -3)])
                continue
            points = [(x + 10 * forward[0], y + 10 * forward[1]),
                      (x - 7 * forward[0] + 6 * side[0], y - 7 * forward[1] + 6 * side[1]),
                      (x - 4 * forward[0], y - 4 * forward[1]),
                      (x - 7 * forward[0] - 6 * side[0], y - 7 * forward[1] - 6 * side[1])]
            pygame.draw.polygon(self.surface, BACKGROUND, points, 5)
            pygame.draw.polygon(self.surface, CAR_COLORS[racer.id % len(CAR_COLORS)], points)
        return positions

    def draw_planner(self):
        self.draw_pit_background()
        self.label("RACE CONTROL  /  ROUTE PLANNER", 48, 98, 14, (246, 125, 84))
        self.label("TRACK EXPLORER", 45, 118, 42, (247, 242, 228))
        self.label("Select vertices on the map or use the arrow keys.", 48, 176, 16, (170, 182, 172))
        self.menu_button((1040, 103, 190, 44), "‹  MAIN MENU", None, lambda: self.go("menu"))
        self.card((40, 220, 800, 530), (21, 33, 32), 12, (58, 73, 68))
        self.menu_button((630, 160, 180, 42), "COMPARE", None, lambda: self.go("compare"))
        self.menu_button((820, 160, 190, 42), "ORDERED: ON" if self.ordered_plan else "ORDERED: OFF", None, self.toggle_ordered_plan)
        profile_name = list(PROFILES)[self.profile_index]
        route = self.planned_route(PROFILES[profile_name])
        graph = self.circuit.graph
        breadth = bfs(graph, self.source)
        depth = dfs(graph, self.source)
        unreachable = set(self.circuit.checkpoints) - set(breadth.parents)
        self.draw_map(PLANNER_MAP, self.circuit, route.edges, route.vertices, unreachable=unreachable)
        self.menu_button((75, 662, 205, 42), "REFUEL PLAN", None, self.open_refuel_plan)
        self.menu_button((292, 662, 205, 42), "ALTERNATIVES", None, self.open_alternatives)
        self.label(f"CHECKPOINTS {len(self.circuit.checkpoints) - len(unreachable)}/{len(self.circuit.checkpoints)} REACHABLE   "
                   f"DFS {len(depth.order)}   "
                   f"Components: {len(weak_components(graph))}   Cycles: {'yes' if has_cycle(graph) else 'no'}   "
                   f"Dead ends: {len(dead_ends(graph, self.circuit.start))}", 75, 715, 14, MUTED)
        self.card((860, 220, 380, 530), (21, 33, 32), 12, (58, 73, 68))
        self.label("ROUTE INTELLIGENCE", 885, 246, 14, (246, 125, 84))
        circuit_name = self.circuit.name
        while self.fonts[24].size(circuit_name)[0] > 330 and len(circuit_name) > 1:
            circuit_name = circuit_name[:-1]
        self.label(circuit_name, 885, 275, 24, (247, 242, 228))
        self.label(f"From {self.source}   →   {'ordered lap' if self.ordered_plan else f'To {self.target}'}", 885, 322, 18, (218, 224, 211))
        self.label(f"Optimized cost   {route.cost:.3f}" if route.vertices else "Destination unreachable", 885, 358, 18, (246, 125, 84))
        self.label(f"Expanded {route.expanded}  /  Relaxed {route.relaxed}", 885, 391, 14, (153, 168, 158))
        self.menu_button((885, 430, 330, 48), f"PRESET: {profile_name.upper()}", None, self.cycle_profile)
        self.menu_button((885, 488, 330, 48), f"ALGORITHM: {self.route_algorithm.upper()}", None, self.toggle_route_algorithm)
        self.menu_button((885, 546, 330, 48), "FIXED SEASON ORDER" if self.pending_championship else "GENERATE CIRCUIT", None, self.generate)
        race_label = (f"START RACE {self.track_index + 1} / {len(self.authored_paths)}"
                      if self.pending_championship else "START QUICK RACE")
        self.menu_button((885, 604, 330, 48), race_label, None, self.start_planned_race, True)
        destinations = self.ordered_destinations() if self.ordered_plan else [self.target]
        pickup_key = (self.source, tuple(destinations), self.resource_graph_signature())
        if pickup_key not in self._pickup_cache:
            self._pickup_cache = {pickup_key: pickup_suggestions(
                self.circuit.graph, self.source, destinations[-1], waypoints=destinations)}
        suggestions = self._pickup_cache[pickup_key]
        selected = [item for item in suggestions if item.dp_selected]
        recommendation = (f"PICKUP {selected[0].vertex} / DP {selected[0].benefit} / GREEDY {int(selected[0].greedy_selected)}"
                          if selected else "NITRO: no feasible pickup within budget")
        self.label((self.validation_message or recommendation)[:42], 885, 675, 14, GOLD)
        route_key = (tuple(route.vertices), tuple(route.edges), self.resource_graph_signature())
        if route.vertices and route_key not in self._refuel_cache:
            self._refuel_cache[route_key] = route_refuelling(self.circuit.graph, route.vertices, route.edges)
        refuelling = self._refuel_cache.get(route_key)
        fuel_message = f"REFUEL PLAN: {refuelling[0] // 3} stop(s), 0.1-unit model" if refuelling is not None else "REFUEL PLAN: no feasible route"
        self.label(fuel_message, 885, 691, 14, MUTED)
        for index, (name, profile) in enumerate(PROFILES.items()):
            candidate = self.planned_route(profile)
            self.label(f"{name}: {candidate.cost:.2f}", 885 + (index % 2) * 160,
                       711 + (index // 2) * 18, 14, MUTED)

    def planned_route(self, profile):
        if not self.ordered_plan:
            return shortest_path(self.circuit.graph, self.source, self.target, profile, self.route_algorithm)
        return checkpoint_route(self.circuit.graph, self.source, self.ordered_destinations(),
                                profile, self.route_algorithm)

    def ordered_destinations(self):
        checkpoints = self.circuit.checkpoints
        if self.source in checkpoints:
            checkpoints = checkpoints[checkpoints.index(self.source) + 1:]
        return checkpoints + [self.circuit.start]

    def toggle_ordered_plan(self):
        self.ordered_plan = not self.ordered_plan

    def open_refuel_plan(self):
        self.refuel_page = 0
        self.go("refuel")

    def resource_graph_signature(self):
        graph = self.circuit.graph
        return (id(graph), tuple((v.id, v.kind, v.active) for v in graph.vertices.values()),
                tuple((e.id, e.source, e.target, e.directed, e.status, e.distance,
                       e.fuel_cost, e.difficulty) for e in graph.edges.values()))

    def refuel_stops(self):
        """Return the selected route and its minimum discrete fuel purchases."""
        route = self.planned_route(PROFILES[list(PROFILES)[self.profile_index]])
        if not route.vertices:
            return route, None
        key = (tuple(route.vertices), tuple(route.edges), self.resource_graph_signature())
        if key not in self._refuel_cache:
            self._refuel_cache[key] = route_refuelling(self.circuit.graph, route.vertices, route.edges)
        plan = self._refuel_cache[key]
        if plan is None:
            return route, None
        return route, [(vertex, amount / 10) for vertex, amount in zip(route.vertices, plan[1]) if amount]

    def draw_refuel_plan(self):
        self.header("01 / Resources", "Refuelling plan",
                    "Minimum stops for the selected route, starting with a full tank.")
        self.nav()
        self.card((40, 220, 1200, 530))
        route, stops = self.refuel_stops()
        if not route.vertices:
            self.label("The selected destination is unreachable.", 75, 270, 20, GOLD)
        elif stops is None:
            self.label("No feasible fuel plan exists for this route.", 75, 270, 20, GOLD)
        elif not stops:
            self.label("No refuelling stops are required for this route.", 75, 270, 20, ACCENT)
        else:
            page_size = 6
            pages = (len(stops) + page_size - 1) // page_size
            self.refuel_page = min(self.refuel_page, pages - 1)
            self.label(f"{len(stops)} STOP(S)  /  PAGE {self.refuel_page + 1} OF {pages}", 75, 260, 14, ACCENT)
            self.label("STATION VERTEX", 75, 300, 14, MUTED)
            self.label("PLANNED FUEL", 400, 300, 14, MUTED)
            for index, (vertex, amount) in enumerate(stops[self.refuel_page * page_size:(self.refuel_page + 1) * page_size]):
                self.label(f"{self.refuel_page * page_size + index + 1:02}   {vertex}", 75, 335 + index * 39, 18)
                self.label(f"{amount:.1f} units", 400, 335 + index * 39, 18)
            if self.refuel_page:
                self.button((75, 590, 180, 45), "PREVIOUS", lambda: setattr(self, "refuel_page", self.refuel_page - 1))
            if self.refuel_page + 1 < pages:
                self.button((275, 590, 180, 45), "NEXT", lambda: setattr(self, "refuel_page", self.refuel_page + 1))
        self.label("At each listed station press F; the game adds up to 40 units.", 75, 655, 16, MUTED)
        self.label("The plan assumes no nitro use or changes to roads or stations.", 75, 680, 16, MUTED)
        self.button((900, 665, 280, 50), "BACK TO PLANNER", lambda: self.go("planner"))

    def open_alternatives(self):
        """Search a bounded set of simple routes between the selected vertices."""
        graph = self.circuit.graph
        paths, self.alternative_truncated = bounded_simple_paths(
            graph, self.source, self.target, limit=6,
            max_length=min(len(graph.vertices), 16), max_states=10000)
        profile = PROFILES[list(PROFILES)[self.profile_index]]
        selected = shortest_path(graph, self.source, self.target, profile, self.route_algorithm)
        self.alternative_paths = [path for path in paths if path != selected.vertices][:5]
        self.alternative_index = 0
        self.go("alternatives")

    def change_alternative(self, direction):
        if self.alternative_paths:
            self.alternative_index = (self.alternative_index + direction) % len(self.alternative_paths)

    def draw_alternatives(self):
        self.header("01 / Explore", "Alternative roads",
                    "Simple routes between the selected vertices; checkpoint order is not enforced here.")
        self.nav()
        graph = self.circuit.graph
        breadth, depth = bfs(graph, self.source), dfs(graph, self.source)
        self.card((40, 220, 800, 530))
        route = self.alternative_paths[self.alternative_index] if self.alternative_paths else []
        profile = PROFILES[list(PROFILES)[self.profile_index]]
        roads = []
        for source, target in zip(route, route[1:]):
            road = min((edge for neighbor, edge in graph.neighbors(source) if neighbor == target),
                       key=lambda edge: (profile.cost(edge), edge.id))
            roads.append(road)
        self.draw_map((60, 242, 760, 480), self.circuit, [road.id for road in roads], route)
        self.label("LIME  /  SELECTED ALTERNATIVE", 75, 715, 14, MUTED)
        self.card((860, 220, 380, 530))
        self.label(f"FROM {self.source}  TO {self.target}", 885, 246, 14, ACCENT)
        minimum = breadth.path_to(self.target)
        self.label(f"BFS minimum: {len(minimum) - 1} roads" if minimum else "BFS: destination unreachable",
                   885, 280, 18)
        self.label(f"DFS visited {len(depth.order)} vertices", 885, 313, 16, MUTED)
        self.label(f"ALTERNATIVE {self.alternative_index + 1} / {len(self.alternative_paths)}"
                   if route else "NO ALTERNATIVE FOUND", 885, 361, 18, GOLD)
        if route:
            self.label(f"{len(roads)} roads   /   cost {sum(profile.cost(edge) for edge in roads):.3f}",
                       885, 397, 16)
            self.label(" > ".join(map(str, route))[:38], 885, 429, 14, MUTED)
        self.button((885, 480, 157, 48), "PREVIOUS", lambda: self.change_alternative(-1))
        self.button((1055, 480, 160, 48), "NEXT", lambda: self.change_alternative(1))
        self.label("At most 5 alternatives shown.", 885, 551, 14, MUTED)
        self.label("Search: 10,000 states, 16 vertices.", 885, 576, 14, MUTED)
        self.label("Results may be incomplete." if self.alternative_truncated else "Search finished within its limits.",
                   885, 601, 14, GOLD if self.alternative_truncated else MUTED)
        self.button((885, 657, 330, 48), "BACK TO PLANNER", lambda: self.go("planner"))

    def draw_settings(self):
        self.draw_pit_background()
        self.label("RACE CONTROL  /  SETUP", 48, 101, 14, (246, 125, 84))
        self.label("CONTROLS & SETTINGS", 45, 124, 42, (247, 242, 228))
        self.label("Get comfortable before the lights go out.", 48, 183, 18, (170, 182, 172))
        self.menu_button((1040, 113, 190, 50), "‹  MAIN MENU", None, lambda: self.go("menu"))
        for rect in ((48, 225, 680, 525), (748, 225, 484, 525)):
            pygame.draw.rect(self.surface, (21, 33, 32), rect, border_radius=12)
            pygame.draw.rect(self.surface, (58, 73, 68), rect, 1, border_radius=12)
        self.label("01   /   DRIVER CONTROLS", 76, 250, 14, (246, 125, 84))
        self.label("Know your inputs", 76, 278, 24, (247, 242, 228))
        controls = (("←  /  →", "Select a road at a junction"),
                    ("ENTER", "Drive along the selected road"),
                    ("N", "Use one nitro charge"),
                    ("F", "Refuel at an available station"),
                    ("SPACE", "Pause or resume the race"),
                    ("ESC", "Return to the main menu"),
                    ("TAB", "Move between buttons; Enter activates"))
        for index, (key, description) in enumerate(controls):
            y = 328 + index * 47
            pygame.draw.rect(self.surface, (37, 49, 47), (76, y, 104, 34), border_radius=5)
            pygame.draw.rect(self.surface, (75, 91, 83), (76, y, 104, 34), 1, border_radius=5)
            self.label(key, 86, y + 6, 16, (247, 242, 228))
            self.label(description, 200, y + 7, 18, (218, 224, 211))
        self.label("Race actions are also available on screen.", 76, 680, 16, (153, 168, 158))
        self.label("Planner: arrows select destination; Shift + arrows select start.", 76, 704, 16, (153, 168, 158))

        self.label("02   /   RACE OPTIONS", 780, 250, 14, (246, 125, 84))
        self.label("Your race, your pace", 780, 278, 24, (247, 242, 228))
        self.label("LAPS PER RACE", 780, 330, 14, (153, 168, 158))
        self.menu_button((780, 354, 420, 53), f"{self.laps_setting} LAPS", None, self.toggle_laps)
        self.label("RACE TIME LIMIT", 780, 427, 14, (153, 168, 158))
        self.menu_button((780, 451, 420, 53), f"{self.limit_setting} SECONDS", None, self.toggle_limit)
        self.label("INTERFACE MOTION", 780, 524, 14, (153, 168, 158))
        self.menu_button((780, 548, 420, 53), "REDUCED" if self.reduced_motion else "FULL", None, self.toggle_motion)
        self.label("Select an option to change it.", 780, 627, 16, (153, 168, 158))
        self.label("Race rules apply equally to all drivers.", 780, 652, 16, (153, 168, 158))

    def toggle_laps(self):
        self.laps_setting = 3 if self.laps_setting == 2 else 2

    def toggle_limit(self):
        options = [180, 240, 360]
        self.limit_setting = options[(options.index(self.limit_setting) + 1) % len(options)]

    def toggle_motion(self):
        self.reduced_motion = not self.reduced_motion
        if self.reduced_motion:
            self.transition_remaining = 0

    def generate(self):
        if self.pending_championship:
            self.validation_message = "Championship circuits follow the fixed season order"
            return
        try:
            self.generation_trace = []
            self.circuit = generate_circuit(int(self.time * 1000), trace=self.generation_trace)
        except ValueError as error:
            self.validation_message = f"Generation failed: {error}"
            return
        self.validation_message = ""
        self._refuel_cache.clear()
        self.source = self.circuit.start
        self.target = self.circuit.checkpoints[min(3, len(self.circuit.checkpoints) - 1)]
        self.generation_started = self.time
        self.go("generation")

    def draw_generation(self):
        self.header("01 / Generate", "Circuit workshop",
                    "Follow the actual generation and validation stages for this seeded track.")
        self.nav()
        self.card((40, 220, 800, 530))
        self.draw_map((60, 242, 760, 480), self.circuit)
        self.label("GENERATED CIRCUIT  /  VALIDATED", 75, 715, 14, ACCENT)
        self.card((860, 220, 380, 530))
        self.label(self.circuit.name.upper(), 885, 245, 20, ACCENT)
        count = len(self.generation_trace) if self.reduced_motion else min(
            len(self.generation_trace), 1 + int(max(0, self.time - self.generation_started) * 2))
        visible = self.generation_trace[:count][-7:]
        for index, step in enumerate(visible):
            y = 285 + index * 45
            self.label(step["stage"].replace("_", " ").upper(), 885, y, 14,
                       GOLD if step["stage"] == "rejected" else ACCENT)
            self.label(step["detail"][:46], 885, y + 19, 14, MUTED)
        self.label(self.validation_message, 885, 611, 14, GOLD)
        self.button((885, 638, 330, 42), "TEST INVALID TRACK", self.demonstrate_rejection)
        self.button((885, 691, 330, 42), "BACK TO PLANNER", lambda: self.go("planner"))

    def draw_comparison(self):
        self.header("01 / Compare", "Route trade-offs", "Each preset optimizes its own normalized, weighted scalar cost.")
        self.nav()
        self.card((40, 220, 1200, 530))
        self.label(f"FROM {self.source} / {'ORDERED LAP' if self.ordered_plan else f'TO {self.target}'}", 75, 250, 14, ACCENT)
        for title, x in (("PRESET", 75), ("DISTANCE", 245), ("TIME", 390), ("FUEL", 520),
                         ("DIFFICULTY", 655), ("OBSTACLE", 805), ("COST", 950)):
            self.label(title, x, 300, 14, MUTED)
        for index, (name, profile) in enumerate(PROFILES.items()):
            route = self.planned_route(profile)
            edges = [self.circuit.graph.edges[edge_id] for edge_id in route.edges]
            values = [name, f"{sum(edge.distance for edge in edges):.1f}",
                      f"{sum(edge.base_time * (1.5 if edge.status == 'restricted' else 1) for edge in edges):.1f}",
                      f"{sum(edge.fuel_cost * (1 + .1 * (edge.difficulty - 1)) for edge in edges):.1f}",
                      f"{sum(edge.difficulty - 1 for edge in edges):.1f}",
                      f"{sum(edge.obstacle for edge in edges):.1f}",
                      f"{route.cost:.3f}" if route.vertices else "unreachable"]
            y = 340 + index * 65
            pygame.draw.line(self.surface, (69, 85, 69), (75, y - 10), (1195, y - 10))
            for value, x in zip(values, (75, 245, 390, 520, 655, 805, 950)):
                self.label(value, x, y, 18, ACCENT if index == self.profile_index else TEXT)
            self.label(self.comparison_path(route.vertices, index), 75, y + 27, 14, MUTED)
        self.label("Scalar costs use different weights; lower scores across presets are not directly comparable.", 75, 640, 16, MUTED)
        self.label(self.validation_message[:90], 75, 615, 14, GOLD)
        self.button((75, 675, 255, 50), "VALIDATE BAD TRACK", self.demonstrate_rejection)
        self.button((350, 675, 255, 50), "SAVE CIRCUIT", self.save_current_circuit)
        self.button((900, 675, 280, 50), "BACK TO PLANNER", lambda: self.go("planner"))

    def comparison_path(self, vertices, row):
        """Reveal the actual route gradually without affecting route selection."""
        if not vertices:
            return "No route"
        if self.reduced_motion:
            visible = vertices
        else:
            step = int(self.time * 3 + row * 2) % (len(vertices) + 6)
            visible = vertices[:min(len(vertices), step + 1)]
        suffix = " ..." if len(visible) < len(vertices) else ""
        return (" → ".join(map(str, visible)) + suffix)[:50]

    def demonstrate_rejection(self):
        invalid = deepcopy(self.circuit)
        for edge in invalid.graph.edges.values():
            edge.shortcut = False
        errors = validate_circuit(invalid)
        self.validation_message = "Rejected: " + (errors[0] if errors else "validation unexpectedly passed")

    def save_current_circuit(self):
        filename = "".join(c.lower() if c.isalnum() else "_" for c in self.circuit.name) + ".json"
        path = self.saved_directory / filename
        try:
            save_circuit(self.circuit, path)
        except (OSError, ValueError) as error:
            self.validation_message = f"Save failed: {error}"
            return
        if path not in self.circuit_paths:
            self.circuit_paths.append(path)
        self.validation_message = f"Saved: {path}"

    def cycle_profile(self):
        self.profile_index = (self.profile_index + 1) % len(PROFILES)

    def toggle_route_algorithm(self):
        self.route_algorithm = "astar" if self.route_algorithm == "dijkstra" else "dijkstra"

    def lab_result(self):
        if self.lab_algorithm in {"BFS", "DFS"}:
            result = (bfs if self.lab_algorithm == "BFS" else dfs)(self.circuit.graph, self.source)
            return result.trace, f"Visited {len(result.order)} vertices  •  examined {result.examined_edges} roads"
        if self.lab_algorithm in {"Dijkstra", "Astar"}:
            result = shortest_path(self.circuit.graph, self.source, self.target, PROFILES[list(PROFILES)[self.profile_index]], self.lab_algorithm.lower())
            return result.trace, f"Expanded {result.expanded} vertices  •  relaxed {result.relaxed} roads"
        trace = []
        if self.lab_algorithm in {"Knapsack", "Greedy"}:
            suggestions = pickup_suggestions(self.circuit.graph, self.source, self.target)
            if not suggestions:
                return [], "No feasible pickup on this track"
            # The gameplay planner evaluates these alternatives independently.
            suggestion = suggestions[0]
            items = [Pickup(suggestion.vertex, suggestion.detour, suggestion.benefit)]
            result = (knapsack if self.lab_algorithm == "Knapsack" else greedy)(items, 10, trace)
            description = f"Pickup {suggestion.vertex}  •  cost {result.cost}  •  benefit {result.benefit}"
        elif self.lab_algorithm == "Backtracking":
            result = _assign_checkpoints([3, 8, 10, 2, 7, 1, 9, 4, 6, 5], 10, trace, _ring_compatible)
            for step in trace:
                step["vertex"] = self.circuit.checkpoints[step["vertex"] - 1]
            description = f"Generator example: {len(result)} placements"
        elif self.lab_algorithm == "Kruskal":
            try:
                graph = Graph()
                for vertex in self.circuit.graph.vertices.values():
                    graph.add_vertex(vertex)
                directed_count = 0
                for edge in self.circuit.graph.edges.values():
                    if edge.directed:
                        directed_count += 1
                    else:
                        graph.add_edge(edge)
                result = kruskal(graph, trace)
                description = f"Accepted {len(result)} roads; excluded {directed_count} one-way"
            except ValueError as error:
                trace = []
                description = str(error)
        elif self.lab_algorithm == "Event heap":
            heap = MinHeap(trace=trace)
            roads = sorted(self.circuit.graph.edges.values(), key=lambda edge: edge.id)[:8]
            for sequence, edge in enumerate(roads):
                heap.push((edge.base_time, edge.difficulty, sequence))
            while heap:
                heap.pop()
            description = "Track road times / difficulty / sequence"
        else:
            values = self.entries if self.entries else self.circuit.checkpoints
            key = ranking_key if self.entries else lambda value: value
            if self.lab_algorithm == "Top-k":
                result = top_k(values, min(3, len(values)), key=key, trace=trace)
            else:
                method = {"Merge sort": merge_sort, "Quick sort": quick_sort, "Heap sort": heap_sort}[self.lab_algorithm]
                result = method(values[::-1], key=key, trace=trace)
            names = [entry.name for entry in result] if self.entries else list(map(str, result))
            label = "Standings" if self.entries else "Track checkpoints"
            description = f"{label}: {', '.join(names[:4])}"
        return trace, description

    def draw_lab(self):
        self.draw_pit_background()
        self.label("RACE CONTROL  /  ALGORITHM LAB", 48, 98, 14, (246, 125, 84))
        self.label("ALGORITHM LAB", 45, 118, 42, (247, 242, 228))
        self.label("Explore real algorithm steps from the selected circuit.", 48, 176, 16, (170, 182, 172))
        self.menu_button((1040, 103, 190, 44), "‹  MAIN MENU", None, lambda: self.go("menu"))
        trace, description = self.lab_result()
        count = min(int(self.lab_step), len(trace))
        steps = trace[:count]
        if self.lab_algorithm == "Backtracking":
            visited = []
            for step in steps:
                if step["action"] == "place checkpoint":
                    visited.append(step["vertex"])
                elif step["action"] == "backtrack" and step["vertex"] in visited:
                    visited.remove(step["vertex"])
        else:
            visited = [step["vertex"] for step in steps if "vertex" in step]
        roads = [step["edge"] for step in steps if "edge" in step]
        self.card((40, 220, 800, 530), (21, 33, 32), 12, (58, 73, 68))
        self.draw_map((60, 242, 760, 375), self.circuit, roads, visited)
        self.card((75, 630, 730, 78), (26, 38, 36), 8, (58, 73, 68))
        if steps:
            current = steps[-1]
            self.label(str(current.get("action", "step")).upper(), 95, 642, 16, (246, 125, 84))
            detail = "   ".join(f"{key}: {value}" for key, value in current.items() if key != "action")
            self.label(detail[:90], 95, 672, 14, MUTED)
        else:
            self.label("READY TO PLAY", 95, 642, 16, (246, 125, 84))
            self.label("Start playback or step forward to inspect the trace.", 95, 672, 14, MUTED)
        self.card((860, 220, 380, 530), (21, 33, 32), 12, (58, 73, 68))
        self.label(f"ALGORITHM {LAB_ALGORITHMS.index(self.lab_algorithm) + 1} / {len(LAB_ALGORITHMS)}", 885, 245, 14, (246, 125, 84))
        self.label(self.lab_algorithm, 885, 276, 30, (247, 242, 228))
        while self.fonts[14].size(description)[0] > 330 and len(description) > 1:
            description = description[:-1]
        self.label(description, 885, 326, 14, MUTED)
        self.label(f"STEP  {count} / {len(trace)}", 885, 365, 18, (246, 125, 84))
        pygame.draw.rect(self.surface, (52, 66, 61), (885, 397, 330, 4), border_radius=2)
        if trace:
            pygame.draw.rect(self.surface, (246, 125, 84), (885, 397, round(330 * count / len(trace)), 4), border_radius=2)
        self.menu_button((885, 411, 157, 48), "PREVIOUS", None, lambda: self.change_lab(-1))
        self.menu_button((1055, 411, 160, 48), "NEXT", None, lambda: self.change_lab(1))
        self.menu_button((885, 469, 157, 48), "PAUSE" if self.lab_playing else "PLAY", None, self.toggle_lab)
        self.menu_button((1055, 469, 160, 48), "STEP +1", None, lambda: self.step_lab(1))
        self.menu_button((885, 527, 157, 48), "RESET", None, self.reset_lab)
        self.menu_button((1055, 527, 160, 48), "STEP -1", None, lambda: self.step_lab(-1))
        self.menu_button((885, 585, 330, 48), f"SPEED: {self.lab_speed / 3:g}x", None, self.change_lab_speed)
        self.label("The trace comes from the game’s", 885, 655, 14, MUTED)
        self.label("own algorithm implementations.", 885, 680, 14, MUTED)

    def change_lab(self, direction):
        self.lab_algorithm = LAB_ALGORITHMS[(LAB_ALGORITHMS.index(self.lab_algorithm) + direction) % len(LAB_ALGORITHMS)]
        self.lab_step = 0

    def toggle_lab(self):
        self.lab_playing = not self.lab_playing

    def change_lab_speed(self):
        speeds = [1.5, 3.0, 6.0, 12.0]
        self.lab_speed = speeds[(speeds.index(self.lab_speed) + 1) % len(speeds)]

    def step_lab(self, amount):
        self.lab_playing = False
        self.lab_step = max(0, self.lab_step + amount)

    def reset_lab(self):
        self.lab_playing = False
        self.lab_step = 0

    def draw_race(self):
        race = self.race
        self.draw_pit_background()
        self.label("RACE CONTROL  /  LIVE RACE", 48, 98, 14, (246, 125, 84))
        race_name = self.circuit.name.upper()
        while self.fonts[42].size(race_name)[0] > 740 and len(race_name) > 1:
            race_name = race_name[:-1]
        self.label(race_name, 45, 118, 42, (247, 242, 228))
        self.label("Choose a road at each junction and follow the checkpoints in order.", 48, 176, 16, (170, 182, 172))
        self.menu_button((1040, 103, 190, 44), "‹  MAIN MENU", None, lambda: self.go("menu"))
        self.card((40, 220, 800, 530), (21, 33, 32), 12, (58, 73, 68))
        human = race.racers[0]
        options = race.options(human) if human.edge_id is None and not human.finished and not human.dnf else []
        if options:
            self.selected_road %= len(options)
        selected_edge = options[self.selected_road][1].id if options else None
        origin = human.edge_target if human.edge_id is not None else human.vertex
        remaining = race.circuit.checkpoints[human.next_checkpoint:] + [race.circuit.start]
        if remaining and origin == remaining[0]:
            remaining = remaining[1:]
        route = checkpoint_route(race.circuit.graph, origin, remaining, PROFILES[list(PROFILES)[self.profile_index]])
        self.draw_map((60, 242, 760, 480), race.circuit, route.edges, racers=race.racers,
                      selected_edge=selected_edge, service_active=race.service_active, race_style=True)
        if not route.vertices and not human.finished and not human.dnf:
            self.label("ROUTE UNAVAILABLE: wait for reopening or choose another road.", 75, 683, 14, PINK)
        self.label("LIME  /  SUGGESTED ROUTE     ORANGE  /  SELECTED ROAD", 75, 715, 14, MUTED)
        self.card((860, 220, 380, 530), (21, 33, 32), 12, (58, 73, 68))
        self.label(f"LAP {min(human.laps + 1, race.laps_required)} / {race.laps_required}", 884, 246, 20, (246, 125, 84))
        self.label(f"{race.elapsed:06.1f}s", 1075, 243, 24, (247, 242, 228))
        self.label(f"FUEL     {human.fuel:05.1f} / 100", 885, 297, 18, (218, 224, 211))
        pygame.draw.rect(self.surface, (52, 66, 61), (885, 330, 325, 8), border_radius=4)
        pygame.draw.rect(self.surface, (244, 103, 64) if human.fuel > 25 else PINK, (885, 330, int(325 * max(human.fuel, 0) / 100), 8), border_radius=4)
        self.label(f"NITRO {human.nitro}/3  [N] BOOST  [F] REFUEL", 885, 353, 16, (246, 125, 84))
        checkpoint_count = len(race.circuit.checkpoints)
        self.label(f"NEXT CHECKPOINT   {human.next_checkpoint + 1 if human.next_checkpoint < checkpoint_count else 'FINISH'}", 885, 391, 16, MUTED)
        if options:
            target, edge = options[self.selected_road]
            self.label(f"ROAD {edge.id} → {target}   {'SHORTCUT' if edge.shortcut else ''}", 885, 440, 20, ACCENT)
            self.label("[←] / [→] select road    [ENTER] drive", 885, 476, 14, MUTED)
            if human.status in {"insufficient fuel for selected road", "selected road unavailable"}:
                self.label(human.status.upper(), 885, 500, 14, PINK)
        elif human.finished:
            self.label("RACE COMPLETE", 885, 440, 20, ACCENT)
        elif human.dnf:
            self.label("DID NOT FINISH", 885, 440, 20, PINK)
        else:
            self.label(human.status.upper()[:25], 885, 440, 20, ACCENT)
        self.label("LIVE POSITIONS", 885, 529, 14, MUTED)
        for index, racer in enumerate(race.results()):
            self.label(f"{index + 1:02}   {racer.name:<8}   CP {min(racer.next_checkpoint, checkpoint_count):02}",
                       885, 558 + 27 * index, 16, CAR_COLORS[racer.id])
        if race.event_log:
            self.label(race.event_log[-1][:38], 885, 694, 14, GOLD)
        if race.over:
            self.menu_button((885, 460, 330, 48), "VIEW RESULTS", None, self.finish_race, True)
        else:
            for rect, title, action in (
                ((40, 756, 165, 40), "PREV ROAD", lambda: self.change_road(-1)),
                ((215, 756, 165, 40), "NEXT ROAD", lambda: self.change_road(1)),
                ((390, 756, 165, 40), "DRIVE", self.drive_selected),
                ((565, 756, 165, 40), "BOOST", lambda: self.race.activate_nitro(0)),
                ((740, 756, 165, 40), "REFUEL", lambda: self.race.refuel(0)),
                ((915, 756, 180, 40), "RESUME" if self.paused else "PAUSE", self.toggle_pause),
            ):
                self.menu_button(rect, title, None, action, title == "DRIVE")

    def change_road(self, direction):
        self.selected_road += direction

    def drive_selected(self):
        human = self.race.racers[0]
        options = self.race.options(human) if human.edge_id is None else []
        if options:
            target, edge = options[self.selected_road % len(options)]
            self.race.choose(0, target, edge.id)

    def toggle_pause(self):
        self.paused = not self.paused

    def finish_race(self):
        if not self.race.over:
            return
        if self.championship and not self.recorded:
            award_results(self.entries, self.race.result_records(self.track_index + 1))
            self.recorded = True
        self.go("dashboard")

    def draw_dashboard(self):
        self.header("04 / Championship", "Race results", "Positions and standings use the same deterministic ordering and tie-breaks.")
        self.nav()
        self.card((40, 220, 1200, 530))
        self.label("RACE CLASSIFICATION", 75, 253, 14, ACCENT)
        self.label("RACER", 170, 299, 14, MUTED)
        self.label("RESULT", 475, 299, 14, MUTED)
        self.label("FASTEST LAP", 700, 299, 14, MUTED)
        self.label("CHAMPIONSHIP POINTS", 920, 299, 14, MUTED)
        by_id = {entry.racer_id: entry for entry in self.entries}
        for index, racer in enumerate(self.race.results()):
            y = 342 + index * 65
            pygame.draw.line(self.surface, (69, 85, 69), (75, y - 12), (1195, y - 12))
            self.label(f"{index + 1:02}", 75, y, 24, CAR_COLORS[racer.id])
            self.label(racer.name, 170, y + 3, 20)
            self.label(f"{racer.finish_time:.1f}s" if racer.finished else "DNF", 475, y + 3, 18)
            self.label(f"{racer.fastest_lap:.1f}s" if math.isfinite(racer.fastest_lap) else "—", 700, y + 3, 18)
            self.label(str(by_id[racer.id].total_points) if racer.id in by_id else "—", 920, y + 3, 18, GOLD)
        if self.championship:
            lead = standings(self.entries)[0]
            label = "CHAMPION" if self.track_index + 1 == len(self.authored_paths) else "CHAMPIONSHIP LEADER"
            self.label(f"{label}   {lead.name}  /  {lead.total_points} PTS", 75, 640, 18, GOLD)
            title = "NEXT RACE" if self.track_index + 1 < len(self.authored_paths) else "FINISH CHAMPIONSHIP"
            self.button((680, 625, 190, 56), "STANDINGS", lambda: self.go("standings"))
            self.button((900, 625, 280, 56), title, self.next_championship_race, selected=True)
        else:
            self.button((900, 625, 280, 56), "RACE AGAIN", lambda: self.start_race(False), selected=True)

    def draw_standings(self):
        self.header("05 / Championship", "Championship standings", "Live top racers and the complete ranking share the same tie-break order.")
        self.nav()
        self.card((40, 220, 1200, 530))
        top = leaders(self.entries, min(self.top_k_count, len(self.entries)))
        self.label(f"LIVE TOP {len(top)}", 75, 250, 14, ACCENT)
        self.button((760, 236, 220, 42), f"SORT: {self.sort_method.upper()}", self.change_sort)
        self.button((1000, 236, 195, 42), f"CHANGE K: {self.top_k_count}", self.change_top_k)
        width = min(330, 1100 // max(1, len(top)) - 20)
        for index, entry in enumerate(top):
            x = 75 + index * (width + 20)
            self.card((x, 285, width, 100), PANEL_LIGHT, 12)
            self.label(f"#{index + 1}  {entry.name}", x + 20, 300, 20, CAR_COLORS[entry.racer_id])
            self.label(f"{entry.total_points} POINTS  /  {entry.wins} WINS", x + 20, 340, 14, MUTED)
        self.label("FULL STANDINGS", 75, 423, 14, ACCENT)
        method = {"Merge": merge_sort, "Quick": quick_sort, "Heap": heap_sort}[self.sort_method]
        ranking = method(self.entries, key=ranking_key)
        agrees = all(sort(self.entries, key=ranking_key) == ranking for sort in (merge_sort, quick_sort, heap_sort))
        for index, entry in enumerate(ranking):
            self.label(f"{index + 1:02}     {entry.name:<10}     {entry.total_points:>3} PTS       {entry.wins} WINS",
                       75, 458 + index * 38, 18, CAR_COLORS[entry.racer_id])
        self.label("ALL THREE SORTS AGREE" if agrees else "SORT RESULTS DIFFER", 75, 625, 14, ACCENT if agrees else PINK)
        self.label("TOP-K HEAP: O(n + k log n)    /    FULL SORT: O(n log n)", 75, 652, 14, MUTED)
        self.button((900, 625, 280, 56), "BACK TO RESULTS", lambda: self.go("dashboard"))

    def change_top_k(self):
        self.top_k_count = self.top_k_count % len(self.entries) + 1

    def change_sort(self):
        methods = ["Merge", "Quick", "Heap"]
        self.sort_method = methods[(methods.index(self.sort_method) + 1) % len(methods)]

    def event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        if event.type == pygame.VIDEORESIZE:
            self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.keyboard_focus = False
            position = self.logical_position(event.pos)
            for rect, action in reversed(self.buttons):
                if rect.collidepoint(position):
                    action()
                    return
            if self.screen == "planner":
                for vertex, point in self.map_positions(PLANNER_MAP, self.circuit).items():
                    if math.dist(point, position) <= 14:
                        self.source, self.target = self.target, vertex
                        break
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.go("menu")
            elif event.key == pygame.K_TAB and self.buttons:
                direction = -1 if getattr(event, "mod", 0) & pygame.KMOD_SHIFT else 1
                if self.keyboard_focus:
                    self.focused_button = (self.focused_button + direction) % len(self.buttons)
                else:
                    self.focused_button = 0 if direction > 0 else len(self.buttons) - 1
                self.keyboard_focus = True
            elif event.key == pygame.K_RETURN and self.keyboard_focus and self.buttons:
                self.buttons[self.focused_button % len(self.buttons)][1]()
            elif self.screen == "planner" and event.key in {pygame.K_LEFT, pygame.K_RIGHT}:
                self.keyboard_focus = False
                vertices = sorted(self.circuit.graph.vertices)
                source = bool(getattr(event, "mod", 0) & pygame.KMOD_SHIFT)
                current = self.source if source else self.target
                selected = vertices[(vertices.index(current) + (1 if event.key == pygame.K_RIGHT else -1)) % len(vertices)]
                if source:
                    self.source = selected
                else:
                    self.target = selected
            elif self.screen == "race":
                if event.key == pygame.K_LEFT:
                    self.keyboard_focus = False
                    self.change_road(-1)
                elif event.key == pygame.K_RIGHT:
                    self.keyboard_focus = False
                    self.change_road(1)
                elif event.key == pygame.K_n:
                    self.race.activate_nitro(0)
                elif event.key == pygame.K_f:
                    self.race.refuel(0)
                elif event.key == pygame.K_SPACE:
                    self.toggle_pause()
                elif event.key == pygame.K_RETURN:
                    self.drive_selected()

    def run(self):
        while self.running:
            delta = min(self.clock.tick(60) / 1000, .1)
            self.time += delta
            for event in pygame.event.get():
                self.event(event)
            if self.screen == "race" and not self.paused:
                self.simulation_clock.advance(delta, self.race.tick)
            if self.screen == "lab" and self.lab_playing:
                self.lab_step += delta * self.lab_speed
            self.buttons = []
            self.background()
            {"menu": self.draw_menu, "settings": self.draw_settings, "planner": self.draw_planner,
             "alternatives": self.draw_alternatives, "generation": self.draw_generation, "refuel": self.draw_refuel_plan,
             "compare": self.draw_comparison, "lab": self.draw_lab,
             "race": self.draw_race, "dashboard": self.draw_dashboard,
             "standings": self.draw_standings}[self.screen]()
            if self.transition_remaining > 0 and self.previous_frame is not None:
                self.transition_remaining = max(0.0, self.transition_remaining - delta)
                previous = self.previous_frame.copy()
                previous.set_alpha(round(255 * (self.transition_remaining / .22) ** 2))
                self.surface.blit(previous, (0, 0))
            self.present()
        pygame.quit()


def main():
    app = App()
    if "--smoke-test" in sys.argv:
        for render in (app.draw_menu, app.draw_settings, app.draw_planner, app.draw_comparison, app.draw_lab):
            app.background()
            render()
        app.start_race(championship=True)
        app.background()
        app.draw_race()
        app.race.elapsed = app.race.time_limit
        app.finish_race()
        app.background()
        app.draw_dashboard()
        app.draw_standings()
        pygame.quit()
    else:
        app.run()
