"""Original low-poly landscapes painted once for the overhead race camera."""

from math import sin
from random import Random

import pygame
from pygame import Vector2


def shade(color, factor):
    return tuple(min(255, round(channel * factor)) for channel in color)


def _harbor_building(surface, x, y, rng):
    # Three visible faces of a dockside warehouse, including its ribbed siding.
    base = Vector2(x, y)
    across = Vector2(rng.randrange(17, 32), 4)
    back = Vector2(7, -8)
    roof = Vector2(0, -rng.randrange(9, 20))
    color = rng.choice(((70, 102, 112), (116, 73, 61), (82, 95, 100)))
    pygame.draw.polygon(surface, (24, 36, 42), (base, base + across + (6, 4),
                                                base + across + back + (6, 4), base + back))
    pygame.draw.polygon(surface, shade(color, .63), (base, base + across, base + across + roof, base + roof))
    pygame.draw.polygon(surface, shade(color, .44), (base + across, base + across + back,
                                                    base + across + back + roof, base + across + roof))
    pygame.draw.polygon(surface, color, (base + roof, base + across + roof,
                                         base + across + back + roof, base + back + roof))
    for i in (.2, .4, .6, .8):
        post = base + across * i
        pygame.draw.line(surface, shade(color, .8), post + (0, -1), post + roof)
    pygame.draw.aaline(surface, shade(color, 1.2), base + roof, base + across + roof)
    pygame.draw.line(surface, (186, 147, 104), base + across * .2 + (0, -4),
                     base + across * .34 + (0, -4), 2)


def _mesa(surface, x, y, rng):
    width = rng.randrange(12, 23)
    height = rng.randrange(10, 22)
    crest = [(x - width, y - 5), (x - width // 2, y - height), (x + width // 3, y - height - 2),
             (x + width, y - 7), (x + 7, y - 3)]
    pygame.draw.polygon(surface, (137, 89, 66), crest)
    pygame.draw.polygon(surface, (85, 54, 49), (crest[0], crest[-1], (x + 6, y + 4), (x - width - 3, y)))
    pygame.draw.polygon(surface, (108, 66, 52), (crest[-1], crest[-2], (x + width + 3, y), (x + 6, y + 4)))
    pygame.draw.aaline(surface, (165, 114, 83), crest[1], crest[2])


def _fir(surface, x, y, rng):
    height = rng.randrange(13, 28)
    pygame.draw.ellipse(surface, (27, 43, 43), (x - 8, y - 3, 21, 6))
    pygame.draw.line(surface, (91, 77, 66), (x, y), (x, y - 7), 2)
    for fraction in (.65, .85, 1):
        top = y - int(height * fraction)
        bottom = top + int(height * .58)
        radius = int(height * .25 / fraction)
        pygame.draw.polygon(surface, (42, 78, 73), ((x, top), (x - radius, bottom), (x, bottom + 2)))
        pygame.draw.polygon(surface, (67, 104, 87), ((x, top), (x, bottom + 2), (x + radius, bottom)))


def _harbor_horizon(surface, rng):
    width = surface.get_width()
    for step, baseline, color in ((13, 55, (80, 82, 97)), (21, 57, (47, 57, 73))):
        for x in range(-5, width, step):
            height = rng.randrange(6, 30)
            span = rng.randrange(8, step + 3)
            pygame.draw.rect(surface, color, (x, baseline - height, span, height))
            if height > 16:
                pygame.draw.line(surface, shade(color, 1.35), (x + 2, baseline - height),
                                 (x + 2, baseline - 2))
                for row in range(baseline - height + 4, baseline - 1, 5):
                    for col in range(x + 4, x + span - 1, 5):
                        if rng.random() < .33:
                            pygame.draw.line(surface, (156, 141, 126), (col, row), (col + 1, row))
    pygame.draw.rect(surface, (45, 69, 80), (0, 57, width, 30))
    for _ in range(140):
        x, y = rng.randrange(width), rng.randrange(58, 86)
        pygame.draw.line(surface, (59, 83, 92), (x, y), (x + rng.randrange(2, 17), y))
    for x in (58, width - 92, width - 50):
        foot = (x, 70)
        top = (x + 2, 26)
        tip = (x + 36, 39)
        for a, b in ((foot, top), ((x - 7, 70), top), (top, tip), ((x - 11, 40), tip)):
            pygame.draw.line(surface, (32, 51, 61), a, b, 2)
        pygame.draw.line(surface, (34, 55, 65), (tip[0] - 4, tip[1]), (tip[0] - 4, 56))
        pygame.draw.circle(surface, (216, 115, 85), top, 1)


def draw_atmosphere(surface, circuit_name, elapsed):
    """Animate only the sky/water band, clear of signs, cars and roads."""
    width = surface.get_width()
    if circuit_name == "Neon Harbor":
        for i in range(20):
            y = 59 + i % 4 * 2
            x = round((71 * i + elapsed * (3 + i % 3)) % width)
            pygame.draw.line(surface, (91, 121, 131), (x, y), (x + 5 + i % 9, y))
    elif circuit_name == "Copper Canyon":
        for i in range(11):
            x = round((i * 83 + 4 * elapsed) % width)
            y = round(17 + 5 * sin(i + elapsed * .25))
            pygame.draw.line(surface, (130, 99, 93), (x, y), (x + 10, y - 1))
    else:
        for layer, color in enumerate(((50, 77, 79), (59, 94, 86), (74, 111, 94))):
            ribbon = [(x, 9 + layer * 2 + 5 * sin(x * .019 + elapsed * .14)
                       + 2 * sin(x * .059 - elapsed * .12)) for x in range(0, width + 8, 8)]
            pygame.draw.lines(surface, color, False, ribbon, 2)


def paint_grandstand(surface, road, positions):
    """Seat rows look inward over one straight. Try both verges for clearance."""
    midpoint, tangent = road.sample(.5)
    normal = Vector2(-tangent.y, tangent.x)
    half = min(48, road.points[0].distance_to(road.points[-1]) * .26)
    if half < 27:
        return False
    center = sum(positions.values(), Vector2()) / len(positions)
    if normal.dot(midpoint - center) < 0:
        normal = -normal
    lot = pygame.Rect(12, 86, surface.get_width() - 24, surface.get_height() - 96)
    for side in (normal, -normal):
        near = midpoint + side * 20
        if all(lot.collidepoint(near + tangent * x + side * 14 + (0, -9))
               for x in (-half, half)) and min(near.distance_to(p) for p in positions.values()) > 34:
            break
    else:
        return False
    for row in range(4):
        front = near + side * (3 * row) - Vector2(0, 2 * row)
        back = front + side * 3 - Vector2(0, 1)
        pygame.draw.polygon(surface, (104, 112, 110), (front - tangent * half, front + tangent * half,
                                                       back + tangent * half, back - tangent * half))
        for i, along in enumerate(range(-int(half) + 3, int(half) - 2, 5)):
            foot = back + tangent * along
            color = (178, 79, 70) if (row + i) % 5 < 3 else (158, 171, 175)
            pygame.draw.line(surface, color, foot, foot - (0, 2), 3)
    top = near + side * 14 - (0, 14)
    for along in (-half, 0, half):
        pygame.draw.line(surface, (42, 49, 53), top + tangent * along + (0, 9), top + tangent * along, 2)
    pygame.draw.line(surface, (200, 205, 202), top - tangent * half, top + tangent * half, 2)
    return True


def paint_scenery(surface, circuit_name, roads):
    """Keep decoration clear of drivable roads, including custom saved layouts."""
    width, height = surface.get_size()
    rng = Random(circuit_name)
    if circuit_name == "Copper Canyon":
        sky, haze, land = (76, 56, 75), (227, 155, 110), (81, 58, 53)
        prop = _mesa
    elif circuit_name == "Neon Harbor":
        sky, haze, land = (40, 53, 83), (177, 140, 133), (48, 62, 65)
        prop = _harbor_building
    else:
        sky, haze, land = (37, 54, 68), (108, 155, 144), (49, 69, 62)
        prop = _fir
    surface.fill(land)
    for y in range(88):
        color = tuple(round(a + (b - a) * y / 87) for a, b in zip(sky, haze))
        pygame.draw.line(surface, color, (0, y), (width, y))
    if prop is not _fir:
        pygame.draw.circle(surface, (233, 182, 143), (width * 3 // 4, 37), 13)
    if prop is _harbor_building:
        _harbor_horizon(surface, rng)
    else:
        for level, color in ((0, shade(haze, .74)), (1, shade(land, 1.22))):
            ridge = [(x, 38 + level * 21 + rng.randrange(-20, 19))
                     for x in range(-20, width + 70, 46)]
            pygame.draw.polygon(surface, color, [(-20, 88), *ridge, (width + 50, 88)])
    # The terrain changes at the shoreline / foot of the mountains.
    pygame.draw.polygon(surface, land, [(0, 84), (width, 64), (width, height), (0, height)])
    for _ in range(width * height // 90):
        x, y = rng.randrange(width), rng.randrange(88, height)
        pygame.draw.line(surface, shade(land, rng.uniform(.90, 1.15)),
                         (x, y), (x + rng.randrange(1, 7), y - 1))
    # Test a footprint around the whole prop against every road segment.
    segments = [(a, b - a, (b - a).length_squared()) for road in roads
                for a, b in zip(road, road[1:])]
    def clear(point):
        for a, delta, length_squared in segments:
            t = max(0, min(1, (point - a).dot(delta) / length_squared)) if length_squared else 0
            if point.distance_squared_to(a + t * delta) < 40 ** 2:
                return False
        return True

    for y in range(101, height - 4, 40):
        for x in range(14, width - 30, 44):
            if rng.random() < .55:
                location = Vector2(x + rng.randrange(-11, 12), y + rng.randrange(-8, 9))
                center = location + ((13, -12) if prop is _harbor_building else (0, -9))
                if clear(center):
                    prop(surface, round(location.x), round(location.y), rng)
