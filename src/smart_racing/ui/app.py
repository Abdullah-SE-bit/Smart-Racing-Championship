"""Pygame presentation; race rules and algorithms stay in their own modules."""

import json
import math
import os
import sys
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from tempfile import NamedTemporaryFile

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
from smart_racing.ui.screens.classification import draw_classification
from smart_racing.ui.components.menu_icons import draw_mode_icon
from smart_racing.ui.visualization.telemetry import drafting_surface, draw_trace_board, endpoint_flag, route_thumbnail
from smart_racing.ui.visualization.race_scene import RaceScene
from smart_racing.ui.components.broadcast import (
    BroadcastGraphics, SCREEN_NAMES, TRANSITION_SECONDS, draw_circuit_model, draw_mark, ease_out, reveal_screen,
)


WIDTH, HEIGHT = 1280, 800
INTRO_DURATION = 4.0
PLANNER_MAP = (60, 242, 760, 400)
BACKGROUND = (12, 14, 19)
PANEL = (23, 26, 33)
PANEL_LIGHT = (40, 44, 53)
TEXT = (244, 245, 248)
MUTED = (183, 190, 201)
ACCENT = (115, 196, 239)  # Suggested route and checkpoint progress.
GOLD = (245, 84, 79)  # Selected road and key race feedback.
PINK = (255, 180, 113)  # Warnings and hazards.
PRIMARY = (197, 35, 43)
EMPHASIS = (255, 102, 100)
BORDER = (65, 72, 84)
GAUGE_TRACK = (54, 61, 72)
CAR_COLORS = (ACCENT, GOLD, PINK, (185, 170, 235))
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
PROFILES = {
    "Balanced": CostProfile(),
    "Speed": CostProfile(distance=.2, time=3, fuel=.2, difficulty=.2, obstacle=.3),
    "Economy": CostProfile(distance=.3, time=.2, fuel=3, difficulty=.3, obstacle=.2),
    "Safety": CostProfile(distance=.3, time=.3, fuel=.3, difficulty=3, obstacle=3),
}
LAB_ALGORITHMS = ["BFS", "DFS", "Dijkstra", "Astar", "Knapsack", "Greedy", "Backtracking",
                  "Kruskal", "Event heap", "Merge sort", "Quick sort", "Heap sort", "Top-k"]


@lru_cache(maxsize=1)
def load_pit_backdrop():
    """Load the packaged original artwork once and scale it for the viewport."""
    image = pygame.image.load(str(ROOT / "assets" / "images" / "pit-lane-night.png")).convert()
    scale = max((WIDTH + 48) / image.get_width(), (HEIGHT + 24) / image.get_height())
    return pygame.transform.smoothscale(image, (round(image.get_width() * scale),
                                                round(image.get_height() * scale)))


class App:
    def __init__(self, *, settings_file=None):
        pygame.init()
        pygame.display.set_caption("Smart Racing Championship")
        self.window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.surface = pygame.Surface((WIDTH, HEIGHT))
        self.pit_backdrop = load_pit_backdrop()
        self.broadcast = BroadcastGraphics(ROOT / "assets" / "fonts", (WIDTH, HEIGHT))
        self.screen_veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.screen_veil.fill((6, 9, 14, 195))
        self.clock = pygame.time.Clock()
        reading_face = str(ROOT / "assets" / "fonts" / "Barlow-Regular.ttf")
        self.fonts = {size: pygame.font.Font(reading_face, size) for size in (14, 16, 18)}
        self.fonts.update({size: self.broadcast.compact[size] for size in (20, 24, 30)})
        self.fonts[42] = self.broadcast.title[42]
        self.symbol_fonts = {size: pygame.font.SysFont("segoeuisymbol,dejavusans", size) for size in self.fonts}
        self.authored_paths = sorted((ROOT / "data" / "circuits").glob("*.json"))
        self.saved_directory = Path.home() / "SmartRacingChampionship" / "circuits"
        self.circuit_paths = self.authored_paths + sorted(self.saved_directory.glob("*.json"))
        self.track_index = 0
        self.circuit = load_circuit(self.circuit_paths[0])
        self.screen = "menu"
        self.running = True
        self.time = 0.0
        self.menu_entered = None
        self.settings_file = settings_file
        self.reduced_motion = self.load_motion_preference()
        self.intro_active = False
        self.intro_elapsed = 0.0
        self.transition_remaining = 0.0
        self.previous_frame = None
        self.simulation_clock = SimulationClock()
        self.buttons = []
        self.focused_button = 0
        self.keyboard_focus = False
        self.race = None
        self.overhead_camera = True
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
        self._lab_key = None
        self._lab_recording = None
        self.paused = False
        self.laps_setting = 2
        self.limit_setting = 240
        self.top_k_count = 3
        self.sort_method = "Merge"
        self.validation_message = ""
        self._refuel_cache = {}
        self._pickup_cache = {}
        self._planner_key = None
        self._planner_routes = {}
        self.refuel_page = 0
        self.alternative_paths = []
        self.alternative_index = 0
        self.alternative_truncated = False
        self.generation_trace = []
        self.generation_started = 0.0

    def label(self, text, x, y, size=18, color=TEXT):
        text = str(text)
        # Barlow does not include the arrows or the hollow diamond used by race controls.
        font = self.symbol_fonts[size] if any(symbol in text for symbol in "←→◇") else self.fonts[size]
        self.surface.blit(font.render(text, True, color), (int(x), int(y)))

    def card(self, rect, color=PANEL, radius=12, border=BORDER):
        pygame.draw.rect(self.surface, color, rect, border_radius=radius)
        pygame.draw.rect(self.surface, border, rect, width=1, border_radius=radius)

    def button(self, rect, title, action, selected=False, subtitle=None):
        self.menu_button(rect, title, subtitle, action, selected)

    def background(self):
        self.surface.fill(BACKGROUND)

    def header(self, eyebrow, title, description):
        self.draw_pit_background()
        self.label(f"RACE CONTROL  /  {eyebrow.upper()}", 48, 98, 14, EMPHASIS)
        self.label(title.upper(), 45, 118, 42, TEXT)
        self.label(description, 48, 176, 16, MUTED)

    def nav(self):
        self.menu_button((1040, 103, 190, 44), "‹  MAIN MENU", None, lambda: self.go("menu"))

    def go(self, screen):
        if screen != self.screen and not self.reduced_motion:
            self.previous_frame = self.surface.copy()
            self.transition_remaining = TRANSITION_SECONDS
        else:
            self.transition_remaining = 0
            self.previous_frame = None
        if screen != self.screen:
            self.buttons = []
            self.focused_button = 0
            if screen == "menu":
                self.menu_entered = None
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
        self.race_scene = None
        self._race_route_key = None
        self._race_route = None
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
        fill = PRIMARY if primary else (46, 51, 61) if hover else (32, 36, 44)
        border = (169, 218, 246) if focused else EMPHASIS if primary else BORDER
        cut = min(9, rect.height // 4, rect.width // 4)
        shape = [(rect.left + cut, rect.top), (rect.right - 1, rect.top),
                 (rect.right - 1, rect.bottom - cut), (rect.right - cut, rect.bottom - 1),
                 (rect.left, rect.bottom - 1), (rect.left, rect.top + cut)]
        pygame.draw.polygon(self.surface, fill, shape)
        pygame.draw.polygon(self.surface, border, shape, 2 if focused else 1)
        if primary or hover or focused:
            pygame.draw.line(self.surface, TEXT if primary else EMPHASIS,
                             (rect.left + 1, rect.top + cut), (rect.left + 1, rect.bottom - 5), 2)
        if (primary or hover or focused) and not self.reduced_motion:
            sweep = int(self.time * 65) % (rect.width + 75) - 40
            highlight = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.polygon(highlight, (255, 255, 255, 20),
                                [(sweep, 0), (sweep + 25, 0),
                                 (sweep - 5, rect.height), (sweep - 30, rect.height)])
            self.surface.blit(highlight, rect.topleft)
        ink = TEXT
        inset = 18
        if rect.width <= 60:
            glyph = self.fonts[24].render(title, True, ink)
            self.surface.blit(glyph, glyph.get_rect(center=rect.center))
        else:
            if self.screen == "menu":
                draw_mode_icon(self.surface, title, (rect.x + 24, rect.centery), TEXT if primary else ACCENT)
                inset = 48
            font = self.broadcast.compact[20 if rect.width < 250 else 24]
            if font.size(title)[0] > rect.width - inset - 26:
                font = self.broadcast.compact[16]
            text = font.render(title, True, ink)
            y = rect.y + 5 if detail else rect.centery - text.get_height() // 2
            self.surface.blit(text, (rect.x + inset, y))
        if detail:
            self.label(detail, rect.x + inset, rect.y + 35, 14,
                       (255, 224, 224) if primary else MUTED)
        if rect.width >= 250:
            x, y = rect.right - 23, rect.centery
            pygame.draw.aalines(self.surface, ink, False, [(x - 3, y - 5), (x + 2, y), (x - 3, y + 5)])
        self.buttons.append((rect, action))

    def draw_menu_circuit(self, rect):
        draw_circuit_model(self.surface, rect, self.circuit, 0 if self.reduced_motion else self.time)

    def draw_pit_background(self):
        x = (WIDTH - self.pit_backdrop.get_width()) // 2
        y = (HEIGHT - self.pit_backdrop.get_height()) // 2
        if not self.reduced_motion:
            x += round(10 * math.sin(self.time * .18))
        self.surface.blit(self.pit_backdrop, (x, y))
        self.surface.blit(self.broadcast.scrim if self.screen == "menu" else self.screen_veil, (0, 0))
        pygame.draw.rect(self.surface, (14, 17, 23), (0, 0, WIDTH, 70))
        pygame.draw.line(self.surface, BORDER, (0, 69), (WIDTH, 69))
        draw_mark(self.surface, 47, 22, .93)
        self.label("SMART RACING CHAMPIONSHIP", 96, 19, 24, TEXT)
        name = self.broadcast.compact[16].render(SCREEN_NAMES[self.screen], True, MUTED)
        self.surface.blit(name, name.get_rect(midright=(WIDTH - 52, 35)))
        pygame.draw.rect(self.surface, EMPHASIS, (WIDTH - 41, 31, 4, 9))

    def start_intro(self):
        """Start a presentation-only sequence; reduced motion opens the menu."""
        self.intro_elapsed = 0.0
        self.intro_active = not self.reduced_motion
        self.buttons = []

    def advance_intro(self, delta):
        if self.intro_active:
            self.intro_elapsed = min(INTRO_DURATION, self.intro_elapsed + max(0.0, delta))
            if self.intro_elapsed >= INTRO_DURATION:
                self.intro_active = False

    def draw_intro(self):
        """A four-second lights-out title sequence, driven only by presentation time."""
        elapsed = self.intro_elapsed
        progress = max(0.0, min(1.0, elapsed / INTRO_DURATION))
        x = (WIDTH - self.pit_backdrop.get_width()) // 2 + round(50 * (progress - .5))
        y = (HEIGHT - self.pit_backdrop.get_height()) // 2
        self.surface.blit(self.pit_backdrop, (x, y))
        self.surface.blit(self.broadcast.scrim, (0, 0))
        # Opening and closing the crop reveals the actual car in the original art.
        crop = round(38 + 74 * (1 - ease_out(elapsed / .85)))
        pygame.draw.rect(self.surface, BACKGROUND, (0, 0, WIDTH, crop))
        pygame.draw.rect(self.surface, BACKGROUND, (0, HEIGHT - crop, WIDTH, crop))
        stage_x = 70
        draw_mark(self.surface, stage_x, 205, .95)
        self.label("SMART RACING CHAMPIONSHIP", stage_x + 48, 201, 24, TEXT)
        self.broadcast.draw_striped_title(self.surface, stage_x - 7, 226, elapsed, INTRO_DURATION)
        rail = pygame.Rect(stage_x, 447, 225, 50)
        pygame.draw.rect(self.surface, (21, 24, 30), rail, border_radius=6)
        pygame.draw.rect(self.surface, BORDER, rail, 1, border_radius=6)
        for index in range(5):
            onset = .55 + .43 * index
            active = onset <= elapsed < 3.45
            center = (rail.x + 26 + 43 * index, rail.centery)
            pygame.draw.circle(self.surface, (8, 10, 13), center, 18)
            pygame.draw.circle(self.surface, (99, 37, 42) if active else (45, 51, 59), center, 14)
            for dx, dy in ((-4, -5), (4, -5), (-7, 1), (0, 1), (7, 1), (-4, 7), (4, 7)):
                pygame.draw.circle(self.surface, (255, 109, 97) if active else (82, 87, 91),
                                   (center[0] + dx, center[1] + dy), 2)
        hint = self.fonts[14].render("Enter, Space, Esc or click to skip", True, TEXT)
        self.surface.blit(hint, hint.get_rect(midright=(WIDTH - 54, HEIGHT - 60)))
        pygame.draw.rect(self.surface, (62, 68, 78), (54, HEIGHT - 38, WIDTH - 108, 2))
        pygame.draw.rect(self.surface, EMPHASIS, (54, HEIGHT - 38, round((WIDTH - 108) * progress), 2))

        fade = min(1.0, elapsed / .35, max(0.0, INTRO_DURATION - elapsed) / .35)
        if fade < 1:
            self.surface.fill((round(255 * fade),) * 3, special_flags=pygame.BLEND_RGB_MULT)

    def draw_menu(self):
        self.draw_pit_background()
        if self.menu_entered is None:
            self.menu_entered = self.time
        progress = 1 if self.reduced_motion else min(1, (self.time - self.menu_entered) / .64)
        self.surface.blit(self.broadcast.menu_shade, (0, 70))
        self.broadcast.draw_menu_title(self.surface, progress)
        self.label("SELECT MODE", 48, 278, 20, TEXT)
        pygame.draw.line(self.surface, BORDER, (148, 293), (468, 293))
        pygame.draw.line(self.surface, EMPHASIS, (148, 293), (148 + round(100 * ease_out(progress)), 293), 2)
        self.menu_button((48, 319, 420, 65), "CHAMPIONSHIP",
                         f"{len(self.authored_paths)} circuits  /  season standings", self.prepare_championship, True)
        self.menu_button((48, 396, 420, 65), "QUICK RACE", "Race the selected circuit", lambda: self.start_race(False))
        self.menu_button((48, 473, 204, 50), "ROUTE PLANNER", None, self.open_quick_planner)
        self.menu_button((264, 473, 204, 50), "ALGORITHM LAB", None, lambda: self.go("lab"))
        self.menu_button((48, 535, 420, 50), "CONTROLS & SETTINGS", None, lambda: self.go("settings"))

        # A single lower third leaves the hero car visible above the circuit selector.
        pygame.draw.rect(self.surface, (18, 22, 29), (0, 615, WIDTH, 130))
        pygame.draw.polygon(self.surface, (29, 36, 45), ((0, 615), (510, 615), (485, 745), (0, 745)))
        pygame.draw.line(self.surface, BORDER, (0, 615), (WIDTH, 615))
        pygame.draw.rect(self.surface, EMPHASIS, (48, 615, 57, 3))
        self.label("SELECT CIRCUIT", 48, 626, 14, MUTED)
        self.menu_button((48, 654, 58, 50), "‹", None, lambda: self.set_track(-1))
        self.menu_button((410, 654, 58, 50), "›", None, lambda: self.set_track(1))
        name = self.circuit.name.upper()
        while self.fonts[24].size(name)[0] > 274 and len(name) > 1:
            name = name[:-1]
        self.label(name, 119, 648, 24, TEXT)
        self.label(f"{self.track_index + 1:02}  /  {len(self.circuit_paths):02}", 120, 683, 14, MUTED)
        self.draw_menu_circuit((525, 616, 236, 128))
        facts = ((len(self.circuit.checkpoints), "CHECKPOINTS"),
                 (sum(edge.shortcut for edge in self.circuit.graph.edges.values()), "SHORTCUTS"),
                 (self.laps_setting, "LAPS"))
        for index, (value, label) in enumerate(facts):
            x = 810 + 151 * index
            pygame.draw.line(self.surface, BORDER, (x - 18, 649), (x - 18, 710))
            self.label(f"{value:02}", x, 636, 42, TEXT)
            self.label(label, x + 1, 693, 14, MUTED)
        for x, width, key, action in ((48, 42, "TAB", "Select"), (162, 58, "ENTER", "Confirm")):
            pygame.draw.rect(self.surface, PANEL, (x, 759, width, 24), border_radius=3)
            pygame.draw.rect(self.surface, BORDER, (x, 759, width, 24), 1, border_radius=3)
            glyph = self.fonts[14].render(key, True, TEXT)
            self.surface.blit(glyph, glyph.get_rect(center=(x + width // 2, 771)))
            self.label(action, x + width + 8, 761, 14, MUTED)

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
        self.surface.blit(drafting_surface(*rect[2:]), rect[:2])
        positions = self.map_positions(rect, circuit)
        selected = set(route or [])
        for edge in circuit.graph.edges.values():
            a, b = positions[edge.source], positions[edge.target]
            color = (97, 53, 47) if edge.status == "blocked" else ((93, 77, 47) if edge.status == "restricted" else (75, 85, 98))
            pygame.draw.line(self.surface, (15, 19, 25), a, b, 20 if race_style else 13)
            pygame.draw.line(self.surface, color, a, b, 15 if race_style else 8)
            if race_style and edge.status == "open":
                pygame.draw.line(self.surface, (47, 54, 64), a, b, 10)
            if edge.id == selected_edge:
                pulse = 0 if self.reduced_motion else int((1 + math.sin(self.time * 5)) / 2 * 2)
                pygame.draw.line(self.surface, GOLD, a, b, 6 + pulse)
            elif edge.id in selected:
                pygame.draw.line(self.surface, ACCENT, a, b, 5)
            elif edge.shortcut:
                pygame.draw.line(self.surface, (184, 157, 115), a, b, 3)
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
                pygame.draw.polygon(self.surface, PINK, [(middle[0], middle[1] - 6),
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
            color = (160, 222, 194) if vertex.kind == "fuel" else (222, 190, 244) if vertex.kind == "nitro" else ACCENT if vertex.id in visited else MUTED
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
                pygame.draw.polygon(self.surface, (9, 12, 17), body, 4)
                pygame.draw.polygon(self.surface, CAR_COLORS[racer.id % len(CAR_COLORS)], body)
                pygame.draw.polygon(self.surface, (26, 32, 42),
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
        self.label("RACE CONTROL  /  ROUTE PLANNER", 48, 98, 14, EMPHASIS)
        self.label("TRACK EXPLORER", 45, 118, 42, TEXT)
        self.label("Select vertices on the map or use the arrow keys.", 48, 176, 16, MUTED)
        self.menu_button((1040, 103, 190, 44), "‹  MAIN MENU", None, lambda: self.go("menu"))
        self.card((40, 220, 800, 530), PANEL, 12, BORDER)
        self.menu_button((630, 160, 180, 42), "COMPARE", None, lambda: self.go("compare"))
        self.menu_button((820, 160, 190, 42), "ORDERED: ON" if self.ordered_plan else "ORDERED: OFF", None, self.toggle_ordered_plan)
        profile_name = list(PROFILES)[self.profile_index]
        route = self.planned_route(PROFILES[profile_name])
        graph = self.circuit.graph
        breadth = bfs(graph, self.source)
        depth = dfs(graph, self.source)
        unreachable = set(self.circuit.checkpoints) - set(breadth.parents)
        positions = self.draw_map(PLANNER_MAP, self.circuit, route.edges, route.vertices, unreachable=unreachable)
        destination = self.circuit.start if self.ordered_plan else self.target
        if self.source == destination:
            endpoint_flag(self, positions[self.source], f"START / FINISH  {self.source}", ACCENT)
        else:
            endpoint_flag(self, positions[self.source], f"FROM  {self.source}", ACCENT)
            endpoint_flag(self, positions[destination], f"TO  {destination}", GOLD, above=False)
        self.menu_button((75, 662, 205, 42), "REFUEL PLAN", None, self.open_refuel_plan)
        self.menu_button((292, 662, 205, 42), "ALTERNATIVES", None, self.open_alternatives)
        self.label(f"CHECKPOINTS {len(self.circuit.checkpoints) - len(unreachable)}/{len(self.circuit.checkpoints)} REACHABLE   "
                   f"DFS {len(depth.order)}   "
                   f"Components: {len(weak_components(graph))}   Cycles: {'yes' if has_cycle(graph) else 'no'}   "
                   f"Dead ends: {len(dead_ends(graph, self.circuit.start))}", 75, 715, 14, MUTED)
        self.card((860, 220, 380, 530), PANEL, 12, BORDER)
        self.label("ROUTE INTELLIGENCE", 885, 246, 14, EMPHASIS)
        circuit_name = self.circuit.name
        while self.fonts[24].size(circuit_name)[0] > 330 and len(circuit_name) > 1:
            circuit_name = circuit_name[:-1]
        self.label(circuit_name, 885, 275, 24, TEXT)
        self.label(f"From {self.source}   →   {'ordered lap' if self.ordered_plan else f'To {self.target}'}", 885, 322, 18, (220, 225, 233))
        self.label(f"Optimized cost   {route.cost:.3f}" if route.vertices else "Destination unreachable", 885, 358, 18, EMPHASIS)
        self.label(f"Expanded {route.expanded}  /  Relaxed {route.relaxed}", 885, 391, 14, MUTED)
        if route.vertices:
            roads = [graph.edges[i] for i in route.edges]
            distance = sum(road.distance for road in roads)
            travel_time = sum(road.base_time * (1.5 if road.status == "restricted" else 1) for road in roads)
            self.label(f"Distance {distance:.1f}   /   Est. {travel_time:.2f}s", 885, 409, 14, MUTED)
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
        destinations = self.ordered_destinations() if self.ordered_plan else [self.target]
        key = (self.resource_graph_signature(), self.source, tuple(destinations), self.route_algorithm,
               self.ordered_plan)
        if key != self._planner_key:
            self._planner_routes.clear()
            self._planner_key = key
        if profile not in self._planner_routes:
            if self.ordered_plan:
                route = checkpoint_route(self.circuit.graph, self.source, destinations, profile, self.route_algorithm)
            else:
                route = shortest_path(self.circuit.graph, self.source, self.target, profile, self.route_algorithm)
            self._planner_routes[profile] = route
        return self._planner_routes[profile]

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

    def resource_graph_signature(self, graph=None):
        graph = self.circuit.graph if graph is None else graph
        return (id(graph), tuple(graph.vertices.values()),
                tuple((e.id, e.source, e.target, e.directed, e.status, e.distance,
                       e.fuel_cost, e.difficulty, e.base_time, e.obstacle, e.shortcut) for e in graph.edges.values()))

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
        self.card((635, 245, 550, 370), (29, 33, 40), 8, BORDER)
        self.label("SELECTED ROUTE", 655, 260, 14, EMPHASIS)
        self.draw_map((650, 280, 520, 315), self.circuit, route.edges, route.vertices)
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
        self.label("BLUE  /  SELECTED ALTERNATIVE", 75, 715, 14, MUTED)
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
        self.label("RACE CONTROL  /  SETUP", 48, 101, 14, EMPHASIS)
        self.label("CONTROLS & SETTINGS", 45, 124, 42, TEXT)
        self.label("Get comfortable before the lights go out.", 48, 183, 18, MUTED)
        self.menu_button((1040, 113, 190, 50), "‹  MAIN MENU", None, lambda: self.go("menu"))
        for rect in ((48, 225, 680, 525), (748, 225, 484, 525)):
            pygame.draw.rect(self.surface, PANEL, rect, border_radius=12)
            pygame.draw.rect(self.surface, BORDER, rect, 1, border_radius=12)
        self.label("01   /   DRIVER CONTROLS", 76, 250, 14, EMPHASIS)
        self.label("Know your inputs", 76, 278, 24, TEXT)
        controls = (("←  /  →", "Select a road at a junction"),
                    ("ENTER", "Drive along the selected road"),
                    ("N", "Use one nitro charge"),
                    ("F", "Refuel at an available station"),
                    ("SPACE", "Pause or resume the race"),
                    ("ESC", "Return to the main menu"),
                    ("TAB", "Move between buttons; Enter activates"))
        for index, (key, description) in enumerate(controls):
            y = 328 + index * 47
            pygame.draw.rect(self.surface, (39, 45, 54), (76, y, 104, 34), border_radius=5)
            pygame.draw.rect(self.surface, (75, 84, 96), (76, y, 104, 34), 1, border_radius=5)
            self.label(key, 86, y + 6, 16, TEXT)
            self.label(description, 200, y + 7, 18, (220, 225, 233))
        self.label("Race actions are also available on screen.", 76, 680, 16, MUTED)
        self.label("Planner: arrows select destination; Shift + arrows select start.", 76, 704, 16, MUTED)

        self.label("02   /   RACE OPTIONS", 780, 250, 14, EMPHASIS)
        self.label("Your race, your pace", 780, 278, 24, TEXT)
        self.label("LAPS PER RACE", 780, 330, 14, MUTED)
        self.menu_button((780, 354, 420, 53), f"{self.laps_setting} LAPS", None, self.toggle_laps)
        self.label("RACE TIME LIMIT", 780, 427, 14, MUTED)
        self.menu_button((780, 451, 420, 53), f"{self.limit_setting} SECONDS", None, self.toggle_limit)
        self.label("INTERFACE MOTION", 780, 524, 14, MUTED)
        self.menu_button((780, 548, 420, 53), "REDUCED" if self.reduced_motion else "FULL", None, self.toggle_motion)
        self.label("Select an option to change it.", 780, 627, 16, MUTED)
        self.label("Race rules apply equally to all drivers.", 780, 652, 16, MUTED)

    def toggle_laps(self):
        self.laps_setting = 3 if self.laps_setting == 2 else 2

    def toggle_limit(self):
        options = [180, 240, 360]
        self.limit_setting = options[(options.index(self.limit_setting) + 1) % len(options)]

    def load_motion_preference(self):
        if self.settings_file is None:
            return False
        try:
            saved = json.loads(self.settings_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        return isinstance(saved, dict) and saved.get("reduced_motion") is True

    def toggle_motion(self):
        self.reduced_motion = not self.reduced_motion
        if self.reduced_motion:
            self.transition_remaining = 0
            self.previous_frame = None
        if self.settings_file is None:
            return
        temporary = None
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(dir=self.settings_file.parent, delete=False, mode="w", encoding="utf-8") as temp:
                temporary = Path(temp.name)
                json.dump({"reduced_motion": self.reduced_motion}, temp)
            os.replace(temporary, self.settings_file)
        except OSError:
            # Keep the selected setting for this session when the directory is read-only.
            pass
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass

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
                         ("DIFFICULTY", 655), ("OBSTACLE", 805), ("COST", 950), ("ROUTE", 1095)):
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
            pygame.draw.line(self.surface, BORDER, (75, y - 10), (1195, y - 10))
            for value, x in zip(values, (75, 245, 390, 520, 655, 805, 950)):
                self.label(value, x, y, 18, ACCENT if index == self.profile_index else TEXT)
            self.label(self.comparison_path(route.vertices, index), 75, y + 27, 14, MUTED)
            route_thumbnail(self.surface, pygame.Rect(1055, y - 6, 130, 57), self.circuit, route)
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
        key = (self.resource_graph_signature(), tuple(self.circuit.checkpoints), self.source, self.target,
               self.profile_index, self.lab_algorithm, tuple((entry.name, ranking_key(entry)) for entry in self.entries))
        if key != self._lab_key:
            self._lab_recording = self._record_lab()
            self._lab_key = key
        return self._lab_recording

    def _record_lab(self):
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
            heap = MinHeap(trace=trace, trace_key=lambda priority: priority)
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
        self.label("RACE CONTROL  /  ALGORITHM LAB", 48, 98, 14, EMPHASIS)
        self.label("ALGORITHM LAB", 45, 118, 42, TEXT)
        self.label("Explore real algorithm steps from the selected circuit.", 48, 176, 16, MUTED)
        self.menu_button((1040, 103, 190, 44), "‹  MAIN MENU", None, lambda: self.go("menu"))
        trace, description = self.lab_result()
        count = min(int(self.lab_step), len(trace))
        self.card((40, 220, 800, 530), PANEL, 12, BORDER)
        draw_trace_board(self, trace, count)
        self.card((75, 630, 730, 78), (29, 33, 40), 8, BORDER)
        if count:
            current = trace[count - 1]
            self.label(str(current.get("action", "step")).upper(), 95, 642, 16, EMPHASIS)
            detail = "   ".join(f"{key}: {value}" for key, value in current.items()
                                if key not in {"action", "keys", "capacities", "values"})
            if not detail:
                detail = f"{len(current.get('values', []))} entries in this operation"
            self.label(detail[:90], 95, 672, 14, MUTED)
        else:
            self.label("READY TO PLAY", 95, 642, 16, EMPHASIS)
            self.label("Start playback or step forward to inspect the trace.", 95, 672, 14, MUTED)
        self.card((860, 220, 380, 530), PANEL, 12, BORDER)
        self.label(f"ALGORITHM {LAB_ALGORITHMS.index(self.lab_algorithm) + 1} / {len(LAB_ALGORITHMS)}", 885, 245, 14, EMPHASIS)
        self.label(self.lab_algorithm, 885, 276, 30, TEXT)
        while self.fonts[14].size(description)[0] > 330 and len(description) > 1:
            description = description[:-1]
        self.label(description, 885, 326, 14, MUTED)
        self.label(f"STEP  {count} / {len(trace)}", 885, 365, 18, EMPHASIS)
        pygame.draw.rect(self.surface, GAUGE_TRACK, (885, 397, 330, 4), border_radius=2)
        if trace:
            pygame.draw.rect(self.surface, EMPHASIS, (885, 397, round(330 * count / len(trace)), 4), border_radius=2)
        self.menu_button((885, 411, 157, 48), "PREVIOUS", None, lambda: self.change_lab(-1))
        self.menu_button((1055, 411, 160, 48), "NEXT", None, lambda: self.change_lab(1))
        self.menu_button((885, 469, 157, 48), "PAUSE" if self.lab_playing else "PLAY", None, self.toggle_lab)
        self.menu_button((1055, 469, 160, 48), "STEP +1", None, lambda: self.step_lab(1))
        self.menu_button((885, 527, 157, 48), "RESET", None, self.reset_lab)
        self.menu_button((1055, 527, 160, 48), "STEP -1", None, lambda: self.step_lab(-1))
        self.menu_button((885, 585, 330, 48), f"SPEED: {self.lab_speed / 3:g}x", None, self.change_lab_speed)
        self.label(self.circuit.name.upper(), 885, 655, 16, TEXT)
        self.label(f"FROM {self.source}   /   TO {self.target}", 885, 685, 14, MUTED)

    def change_lab(self, direction):
        self.lab_algorithm = LAB_ALGORITHMS[(LAB_ALGORITHMS.index(self.lab_algorithm) + direction) % len(LAB_ALGORITHMS)]
        self.lab_step = 0

    def toggle_lab(self):
        if not self.lab_playing and self.lab_step >= len(self.lab_result()[0]):
            self.lab_step = 0
        self.lab_playing = not self.lab_playing

    def change_lab_speed(self):
        speeds = [1.5, 3.0, 6.0, 12.0]
        self.lab_speed = speeds[(speeds.index(self.lab_speed) + 1) % len(speeds)]

    def step_lab(self, amount):
        self.lab_playing = False
        self.lab_step = max(0, min(self.lab_step, len(self.lab_result()[0])) + amount)

    def reset_lab(self):
        self.lab_playing = False
        self.lab_step = 0

    def draw_race(self):
        race = self.race
        self.draw_pit_background()
        self.label("RACE CONTROL  /  LIVE RACE", 48, 98, 14, EMPHASIS)
        race_name = self.circuit.name.upper()
        while self.fonts[42].size(race_name)[0] > 740 and len(race_name) > 1:
            race_name = race_name[:-1]
        self.label(race_name, 45, 118, 42, TEXT)
        self.label("Choose a road at each junction and follow the checkpoints in order.", 48, 176, 16, MUTED)
        self.menu_button((806, 103, 220, 44), "VIEW 2D MAP" if self.overhead_camera else "VIEW 3D CIRCUIT",
                         None, self.toggle_race_camera)
        self.menu_button((1040, 103, 190, 44), "‹  MAIN MENU", None, lambda: self.go("menu"))
        self.card((40, 220, 800, 530), PANEL, 12, BORDER)
        human = race.racers[0]
        options = race.options(human) if human.edge_id is None and not human.finished and not human.dnf else []
        if options:
            self.selected_road %= len(options)
        selected_edge = options[self.selected_road][1].id if options else None
        origin = human.edge_target if human.edge_id is not None else human.vertex
        remaining = race.circuit.checkpoints[human.next_checkpoint:] + [race.circuit.start]
        if remaining and origin == remaining[0]:
            remaining = remaining[1:]
        graph = race.circuit.graph
        profile = PROFILES[list(PROFILES)[self.profile_index]]
        key = (origin, tuple(remaining), profile, self.resource_graph_signature(graph))
        if key != self._race_route_key:
            self._race_route = checkpoint_route(graph, origin, remaining, profile)
            self._race_route_key = key
        route = self._race_route
        if self.overhead_camera:
            viewport = self.surface.subsurface((42, 222, 796, 455))
            if self.race_scene is None:
                self.race_scene = RaceScene(race.circuit, viewport.get_size(), self.fonts[14])
            self.race_scene.draw(viewport, race, route.edges, selected_edge, CAR_COLORS, not self.reduced_motion)
        else:
            self.draw_map((60, 242, 760, 425), race.circuit, route.edges, racers=race.racers,
                          selected_edge=selected_edge, service_active=race.service_active, race_style=True)
        if not route.vertices and not human.finished and not human.dnf:
            self.label("ROUTE UNAVAILABLE: wait for reopening or choose another road.", 75, 683, 14, PINK)
        pygame.draw.line(self.surface, ACCENT, (65, 722), (85, 722), 3)
        self.label("Suggested route", 94, 711, 16, TEXT)
        pygame.draw.line(self.surface, GOLD, (255, 722), (275, 722), 4)
        self.label("Selected road", 284, 711, 16, TEXT)
        self.label("F  Fuel     N  Nitro", 523, 711, 16, MUTED)
        pygame.draw.polygon(self.surface, PINK, ((684, 715), (691, 722), (684, 729), (677, 722)), 2)
        self.label("Hazard", 701, 711, 16, MUTED)
        self.card((860, 220, 380, 530), PANEL, 12, BORDER)
        self.label(f"LAP {min(human.laps + 1, race.laps_required)} / {race.laps_required}", 884, 246, 20, EMPHASIS)
        minutes, seconds = divmod(race.elapsed, 60)
        self.label(f"{int(minutes):02}:{seconds:05.2f}", 1075, 243, 24, TEXT)
        self.label(f"FUEL     {human.fuel:05.1f} / 100", 885, 297, 18, (220, 225, 233))
        pygame.draw.rect(self.surface, GAUGE_TRACK, (885, 330, 325, 8), border_radius=4)
        pygame.draw.rect(self.surface, PRIMARY if human.fuel > 25 else PINK, (885, 330, int(325 * max(human.fuel, 0) / 100), 8), border_radius=4)
        self.label(f"NITRO {human.nitro}/3  [N] BOOST  [F] REFUEL", 885, 353, 16, EMPHASIS)
        for charge in range(3):
            color = EMPHASIS if charge < human.nitro else GAUGE_TRACK
            pygame.draw.rect(self.surface, color, (1148 + charge * 21, 360, 16, 8), border_radius=2)
        checkpoint_count = len(race.circuit.checkpoints)
        self.label(f"NEXT CHECKPOINT   {human.next_checkpoint + 1 if human.next_checkpoint < checkpoint_count else 'FINISH'}", 885, 391, 16, MUTED)
        for checkpoint in range(checkpoint_count):
            left = 885 + round(checkpoint * 325 / checkpoint_count)
            right = 885 + round((checkpoint + 1) * 325 / checkpoint_count) - 3
            color = ACCENT if checkpoint < human.next_checkpoint else GAUGE_TRACK
            pygame.draw.rect(self.surface, color, (left, 417, max(1, right - left), 4), border_radius=2)
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
        elif human.edge_id is not None:
            self.label(f"ROAD {human.edge_id}   /   TO VERTEX {human.edge_target}", 885, 440, 20, ACCENT)
            status = f"NITRO   {human.nitro_remaining:.1f}s" if human.nitro_remaining > 0 else "ON TRACK"
            self.label(status, 885, 475, 14, TEXT)
            self.label(f"{human.edge_progress:.0%}", 1167, 474, 16, MUTED)
            pygame.draw.rect(self.surface, GAUGE_TRACK, (885, 501, 325, 3))
            pygame.draw.rect(self.surface, ACCENT, (885, 501, round(325 * human.edge_progress), 3))
        else:
            self.label(human.status.upper()[:25], 885, 440, 20, ACCENT)
        self.label("LIVE POSITIONS", 885, 529, 14, MUTED)
        for index, racer in enumerate(race.results()):
            if racer.id == human.id:
                pygame.draw.rect(self.surface, (38, 45, 55), (879, 554 + 27 * index, 335, 24), border_radius=4)
            y = 555 + 27 * index
            pygame.draw.rect(self.surface, CAR_COLORS[racer.id % len(CAR_COLORS)], (884, y + 4, 3, 15))
            self.label(f"{index + 1:02}", 897, y, 16, MUTED)
            self.label(racer.name, 938, y, 20, TEXT)
            state = "FIN" if racer.finished else "DNF" if racer.dnf else f"CP  {racer.next_checkpoint:02}"
            self.label(state, 1152, y, 16, MUTED)
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

    def toggle_race_camera(self):
        self.overhead_camera = not self.overhead_camera

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
        draw_classification(self, CAR_COLORS)

    def draw_standings(self):
        self.draw_pit_background()
        self.label("RACE CONTROL  /  CHAMPIONSHIP", 48, 98, 14, EMPHASIS)
        self.label("CHAMPIONSHIP STANDINGS", 45, 118, 42, TEXT)
        self.label(f"ROUND {self.track_index + 1:02}   /   {self.circuit.name.upper()}", 48, 176, 16, MUTED)
        self.menu_button((1040, 103, 190, 44), "‹  MAIN MENU", None, lambda: self.go("menu"))
        self.card((40, 220, 1200, 530), PANEL, 12, BORDER)
        top = leaders(self.entries, min(self.top_k_count, len(self.entries)))
        self.label(f"LIVE TOP {len(top)}", 75, 250, 14, EMPHASIS)
        self.menu_button((760, 236, 220, 42), f"SORT: {self.sort_method.upper()}", None, self.change_sort)
        self.menu_button((1000, 236, 195, 42), f"CHANGE K: {self.top_k_count}", None, self.change_top_k)
        width = (1120 - 12 * (max(1, len(top)) - 1)) // max(1, len(top))
        for index, entry in enumerate(top):
            x = 75 + index * (width + 12)
            color = CAR_COLORS[entry.racer_id % len(CAR_COLORS)]
            self.card((x, 296, width, 94), (31, 36, 45), 4, BORDER)
            pygame.draw.line(self.surface, color, (x + 8, 297), (x + width - 8, 297), 3)
            self.label(f"#{index + 1}  {entry.name}", x + 16, 308, 24, TEXT)
            self.label(f"{entry.total_points} PTS    /    {entry.wins} WINS", x + 16, 351, 16, color)
        for heading, x in (("POS", 75), ("DRIVER", 142), ("CHAMPIONSHIP POINTS", 350),
                           ("WINS", 900), ("BEST LAP", 1010)):
            self.label(heading, x, 417, 14, MUTED)
        method = {"Merge": merge_sort, "Quick": quick_sort, "Heap": heap_sort}[self.sort_method]
        ranking = method(self.entries, key=ranking_key)
        agrees = all(sort(self.entries, key=ranking_key) == ranking for sort in (merge_sort, quick_sort, heap_sort))
        lead_points = max(1, ranking[0].total_points) if ranking else 1
        for index, entry in enumerate(ranking):
            y = 452 + index * 38
            color = CAR_COLORS[entry.racer_id % len(CAR_COLORS)]
            self.label(f"{index + 1:02}", 75, y, 20, color)
            self.label(entry.name, 142, y, 20, TEXT)
            self.label(str(entry.total_points), 350, y, 20, TEXT)
            pygame.draw.rect(self.surface, GAUGE_TRACK, (408, y + 10, 430, 9), border_radius=3)
            length = round(430 * entry.total_points / lead_points)
            if length:
                pygame.draw.rect(self.surface, color, (408, y + 10, length, 9), border_radius=3)
            self.label(str(entry.wins), 900, y, 18, TEXT)
            self.label(f"{entry.best_fastest_lap:.2f}s" if math.isfinite(entry.best_fastest_lap) else "—",
                       1010, y, 18, TEXT)
        self.label("ALL THREE SORTS AGREE" if agrees else "SORT RESULTS DIFFER", 75, 625, 14, ACCENT if agrees else PINK)
        self.label("TOP-K HEAP: O(n log(k+1))    /    FULL SORT: O(n log n)", 75, 652, 14, MUTED)
        self.menu_button((900, 625, 280, 56), "BACK TO RESULTS", None, lambda: self.go("dashboard"))

    def change_top_k(self):
        self.top_k_count = self.top_k_count % len(self.entries) + 1

    def change_sort(self):
        methods = ["Merge", "Quick", "Heap"]
        self.sort_method = methods[(methods.index(self.sort_method) + 1) % len(methods)]

    def event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.VIDEORESIZE:
            self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            return
        if self.intro_active:
            if ((event.type == pygame.KEYDOWN and event.key in {pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE})
                    or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)):
                self.intro_active = False
                self.buttons = []
            return
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
        self.start_intro()
        while self.running:
            delta = min(self.clock.tick(60) / 1000, .1)
            self.time += delta
            for event in pygame.event.get():
                self.event(event)
            if not self.running:
                break
            if self.intro_active:
                self.advance_intro(delta)
                if self.intro_active:
                    self.draw_intro()
                    self.present()
                    continue
            if self.screen == "race" and not self.paused:
                self.simulation_clock.advance(delta, self.race.tick)
            if self.screen == "lab" and self.lab_playing:
                length = len(self.lab_result()[0])
                self.lab_step = min(length, self.lab_step + delta * self.lab_speed)
                self.lab_playing = self.lab_step < length
            self.buttons = []
            self.background()
            {"menu": self.draw_menu, "settings": self.draw_settings, "planner": self.draw_planner,
             "alternatives": self.draw_alternatives, "generation": self.draw_generation, "refuel": self.draw_refuel_plan,
             "compare": self.draw_comparison, "lab": self.draw_lab,
             "race": self.draw_race, "dashboard": self.draw_dashboard,
             "standings": self.draw_standings}[self.screen]()
            if self.transition_remaining > 0 and self.previous_frame is not None:
                self.transition_remaining = max(0.0, self.transition_remaining - delta)
                reveal_screen(self.surface, self.previous_frame, 1 - self.transition_remaining / TRANSITION_SECONDS)
                if self.transition_remaining == 0:
                    self.previous_frame = None
            self.present()
        pygame.quit()


def main():
    smoke_test = "--smoke-test" in sys.argv
    settings_file = None if smoke_test else Path.home() / "SmartRacingChampionship" / "preferences.json"
    app = App(settings_file=settings_file)
    if smoke_test:
        app.start_intro()
        app.advance_intro(1.5)
        app.draw_intro()
        app.advance_intro(INTRO_DURATION)
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
