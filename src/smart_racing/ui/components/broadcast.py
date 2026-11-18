"""REDLINE title treatment, track miniature and screen-to-screen compositing."""

import math

import pygame


INK = (247, 246, 241)
RED = (242, 66, 63)
TRANSITION_SECONDS = .28
SCREEN_NAMES = {"menu": "MAIN MENU", "settings": "SETUP", "planner": "STRATEGY",
                "alternatives": "ALTERNATIVE ROUTES", "generation": "CIRCUIT WORKSHOP",
                "refuel": "FUEL STRATEGY", "compare": "ROUTE COMPARISON", "lab": "ALGORITHM LAB",
                "race": "ON TRACK", "dashboard": "CLASSIFICATION", "standings": "STANDINGS"}


def ease_out(value):
    return 1 - (1 - max(0.0, min(1.0, value))) ** 3


def draw_mark(surface, x, y, scale=1):
    """The split ribbon forms the R in the game's pit-wall wordmark."""
    pieces = (
        ((9, 0), (34, 0), (29, 7), (7, 7)),
        ((6, 10), (27, 10), (22, 16), (14, 16), (23, 27), (13, 27), (5, 17), (0, 23)),
    )
    for piece in pieces:
        points = [(round(x + px * scale), round(y + py * scale)) for px, py in piece]
        pygame.draw.polygon(surface, RED, points)
        pygame.draw.aalines(surface, RED, True, points)


class BroadcastGraphics:
    def __init__(self, font_directory, size):
        italic = str(font_directory / "BarlowCondensed-BoldItalic.ttf")
        upright = str(font_directory / "BarlowCondensed-SemiBold.ttf")
        self.title = {px: pygame.font.Font(italic, px) for px in (42, 104, 170)}
        self.compact = {px: pygame.font.Font(upright, px) for px in (16, 20, 24, 30)}
        self.menu_wordmark = self.title[104].render("REDLINE", True, INK)
        self.intro_wordmark = self.title[170].render("REDLINE", True, INK)
        # One cached scrim preserves the photo's highlights and darkens text areas.
        width, height = size
        scrim = pygame.Surface(size, pygame.SRCALPHA)
        for y in range(height):
            floor = max(0, (y - height * .76) / (height * .24))
            pygame.draw.line(scrim, (7, 10, 15, round(15 + floor * 202)), (0, y), (width, y))
        self.scrim = scrim

    def draw_striped_title(self, surface, x, y, elapsed, duration):
        """Reveal the three slices of the lockup, then let the lights release it."""
        mark = self.intro_wordmark
        release = ease_out((elapsed - (duration - .42)) / .42)
        for band, (start, end) in enumerate(((0, .43), (.43, .63), (.63, 1))):
            top = round(mark.get_height() * start)
            bottom = round(mark.get_height() * end)
            reveal = ease_out((elapsed - .18 - .09 * band) / .72)
            if reveal == 0:
                continue
            travel = 26 + 30 * band
            destination = (round(x - travel * (1 - reveal) + travel * release), y + top)
            surface.blit(mark, destination, (0, top, round(mark.get_width() * reveal), bottom - top))


def draw_circuit_model(surface, rect, circuit, seconds):
    """An orthographic turntable of the selected circuit, with its real lap path."""
    rect = pygame.Rect(rect)
    vertices = circuit.graph.vertices
    yaw = -.20 + .12 * math.sin(seconds * .34)
    direction_x, direction_z = math.cos(yaw), math.sin(yaw)
    corners = {}
    for key, vertex in vertices.items():
        x, z = vertex.x, vertex.y
        corners[key] = (x * direction_x - z * direction_z, .58 * (x * direction_z + z * direction_x))
    min_x, max_x = min(x for x, _ in corners.values()), max(x for x, _ in corners.values())
    min_z, max_z = min(z for _, z in corners.values()), max(z for _, z in corners.values())
    scale = min((rect.width - 20) / max(1, max_x - min_x), (rect.height - 22) / max(1, max_z - min_z))
    points = {key: (round(rect.centerx + scale * (x - (min_x + max_x) / 2)),
                    round(rect.centery - 2 + scale * (z - (min_z + max_z) / 2)))
              for key, (x, z) in corners.items()}
    route = [points[key] for key in circuit.main_route]
    if len(route) < 2:
        return
    for edge in circuit.graph.edges.values():
        pygame.draw.aaline(surface, (99, 111, 125) if edge.shortcut else (53, 62, 75),
                           points[edge.source], points[edge.target])
    for drop, color, width in ((5, (53, 24, 31), 6), (2, (145, 43, 45), 5), (0, INK, 3)):
        path = [(x, z + drop) for x, z in route]
        pygame.draw.lines(surface, color, False, path, width)
        pygame.draw.aalines(surface, color, False, path)
    lengths = [math.dist(a, b) for a, b in zip(route, route[1:])]
    total = sum(lengths)
    if total:
        distance = seconds * 46 % total
        for (a, b), length in zip(zip(route, route[1:]), lengths):
            if length and distance <= length:
                position = pygame.Vector2(a).lerp(b, distance / length)
                pygame.draw.circle(surface, (18, 21, 27), position, 6)
                pygame.draw.circle(surface, RED, position, 4)
                break
            distance -= length


def reveal_screen(surface, previous, progress):
    """Sweep away strips of the outgoing frame over the already active new screen."""
    if progress >= 1:
        return
    if progress <= 0:
        surface.blit(previous, (0, 0))
        return
    width, height = surface.get_size()
    band_height = 16
    for top in range(0, height, band_height):
        # The lower edge trails the top to form a single angled cut.
        delay = .10 * top / height
        x = round(width * ease_out((progress - delay) / .90))
        if x < width:
            strip = (x, top, width - x, min(band_height, height - top))
            surface.blit(previous, (x, top), strip)
            if x > 0:
                pygame.draw.rect(surface, RED, (x - 2, top, 2, strip[3]))
