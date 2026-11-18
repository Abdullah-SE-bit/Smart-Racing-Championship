"""A fixed overhead 3D camera for the live race. All geometry is presentation-only."""

from collections import defaultdict
from math import cos, sin, sqrt

import pygame
from pygame import Vector2

from .circuit_scenery import draw_atmosphere, paint_grandstand, paint_scenery, shade


ASPHALT = (54, 60, 65)
INK = (17, 23, 29)
WHITE = (238, 239, 229)
SUGGESTED = (115, 196, 239)
SELECTED = (245, 84, 79)
HAZARD = (255, 180, 113)
FUEL = (160, 222, 194)
NITRO = (222, 190, 244)
PITCH_SINE = .72
HEIGHT_FACTOR = sqrt(1 - PITCH_SINE ** 2)


def _unit(vector):
    return vector.normalize() if vector.length_squared() else Vector2(1, 0)


class Road:
    """A road has one centreline for the asphalt, navigation overlays and cars."""

    def __init__(self, start, end, lane_offset):
        delta = end - start
        normal = _unit(Vector2(-delta.y, delta.x))
        self.points = [start]
        if lane_offset:
            for t in (.25, .5, .75):
                self.points.append(start + delta * t + normal * (4 * t * (1 - t) * lane_offset))
        self.points.append(end)

    def sample(self, progress):
        segment = max(0, min(1, progress)) * (len(self.points) - 1)
        i = min(int(segment), len(self.points) - 2)
        a, b = self.points[i:i + 2]
        return a.lerp(b, segment - i), _unit(b - a)


def _roads(circuit, positions):
    parallel = defaultdict(list)
    for edge in circuit.graph.edges.values():
        parallel[tuple(sorted((edge.source, edge.target)))].append(edge)
    roads = {}
    for group in parallel.values():
        for i, edge in enumerate(sorted(group, key=lambda edge: edge.id)):
            offset = (i - (len(group) - 1) / 2) * 24
            if edge.source > edge.target:
                offset = -offset
            roads[edge.id] = Road(positions[edge.source], positions[edge.target], offset)
    return roads


def _project_floor(circuit, size):
    # Yaw around the vertical axis and pitch an orthographic camera down.
    # Ground distances share one scale, independent of a track's coordinate units.
    angle = -.14
    raw = {v.id: Vector2(v.x * cos(angle) - v.y * sin(angle),
                         (v.x * sin(angle) + v.y * cos(angle)) * PITCH_SINE)
           for v in circuit.graph.vertices.values()}
    x0, x1 = min(p.x for p in raw.values()), max(p.x for p in raw.values())
    y0, y1 = min(p.y for p in raw.values()), max(p.y for p in raw.values())
    width, height = size
    scale = min((width - 115) / max(1, x1 - x0), (height - 135) / max(1, y1 - y0))
    center = Vector2((x0 + x1) / 2, (y0 + y1) / 2)
    origin = Vector2(width / 2, height / 2 + 32)
    return {vertex: (point - center) * scale + origin for vertex, point in raw.items()}


def _car(surface, point, heading, color, boosting, player):
    # Reconstruct the two horizontal chassis axes from the projected road
    # heading; height then has a separate camera-space component.
    ahead = _unit(Vector2(heading.x, heading.y / PITCH_SINE))
    across = Vector2(-ahead.y, ahead.x)
    def at(length, width, height=0):
        ground = ahead * length + across * width
        return point + Vector2(ground.x, ground.y * PITCH_SINE - height * HEIGHT_FACTOR)

    shadow = [at(-11, -5), at(8, -6), at(13, 0), at(9, 7), at(-10, 7)]
    pygame.draw.polygon(surface, (27, 32, 35), [p + (2, 3) for p in shadow])
    if boosting:
        pygame.draw.polygon(surface, SUGGESTED, [at(-9, -2), at(-20, 0), at(-9, 2)])
    outline = [(-10, -4), (-6, -6), (5, -6), (12, -3), (12, 3), (5, 6), (-6, 6), (-10, 4)]
    for along in (-6, 7):
        pygame.draw.line(surface, INK, at(along, -6), at(along, 6), 5)
    lower = [at(x, y) for x, y in outline]
    deck = [at(x, y, 3) for x, y in outline]
    pygame.draw.polygon(surface, shade(color, .53), lower)
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        if (lower[j] - lower[i]).cross(Vector2(0, 1)) < 0:
            pygame.draw.polygon(surface, shade(color, .62), [lower[i], lower[j], deck[j], deck[i]])
    pygame.draw.polygon(surface, color, deck)
    pygame.draw.aalines(surface, shade(color, .75), True, deck)
    roof = [at(-5, -3, 4), at(1, -3, 7), at(5, -2, 4), at(5, 2, 4),
            at(1, 3, 7), at(-5, 3, 4)]
    pygame.draw.polygon(surface, (38, 54, 67), roof)
    pygame.draw.line(surface, (147, 189, 202), roof[1], roof[-2], 1)
    pygame.draw.line(surface, INK, at(-9, -6, 4), at(-9, 6, 4), 3)
    for side in (-1, 1):
        pygame.draw.line(surface, WHITE, at(10, side * 3, 3), at(8, side * 4, 3), 2)
    if player:
        x, y = point
        pin = [(x - 5, y - 21), (x + 5, y - 21), (x, y - 15)]
        pygame.draw.polygon(surface, INK, pin, 3)
        pygame.draw.polygon(surface, WHITE, pin)


class RaceScene:
    def __init__(self, circuit, size, font):
        self.positions = _project_floor(circuit, size)
        self.roads = _roads(circuit, self.positions)
        self.base = pygame.Surface(size)
        self.signs = {}
        self.font = font
        paint_scenery(self.base, circuit.name, [r.points for r in self.roads.values()])
        main_pairs = {tuple(sorted(pair)) for pair in zip(circuit.main_route, circuit.main_route[1:])}
        main_ids = {edge.id for edge in circuit.graph.edges.values()
                    if not edge.shortcut and tuple(sorted((edge.source, edge.target))) in main_pairs}
        stands = 0
        for edge_id in sorted(main_ids):
            road = self.roads[edge_id]
            if abs(road.sample(.5)[1].y) < .3 and paint_grandstand(self.base, road, self.positions):
                stands += 1
                if stands == 2:
                    break
        for edge in circuit.graph.edges.values():
            self._paint_road(self.roads[edge.id], edge.id in main_ids, edge.shortcut)
        start = self.positions[circuit.start]
        pygame.draw.rect(self.base, INK, (start.x - 8, start.y - 6, 16, 12))
        for x in range(4):
            for y in range(3):
                if (x + y) % 2 == 0:
                    pygame.draw.rect(self.base, WHITE, (start.x - 8 + x * 4, start.y - 6 + y * 4, 4, 4))

    def _paint_road(self, road, main, shortcut):
        width = 18 if main else 13
        for a, b in zip(road.points, road.points[1:]):
            if a == b:
                continue
            normal = _unit(Vector2(a.y - b.y, b.x - a.x))
            pygame.draw.line(self.base, (30, 36, 37), a + (1, 3), b + (1, 3), width + 5)
            pygame.draw.line(self.base, (138, 139, 126) if main else (92, 101, 100), a, b, width + 3)
            pygame.draw.line(self.base, ASPHALT if main else (60, 65, 66), a, b, width)
            length = a.distance_to(b)
            for distance in range(0, int(length), 16):
                start = a.lerp(b, distance / length)
                end = a.lerp(b, min(1, (distance + 7) / length))
                if main:
                    curb = normal * (width / 2)
                    pygame.draw.line(self.base, (174, 85, 77), start + curb, end + curb, 3)
                pygame.draw.line(self.base, (192, 161, 112) if shortcut else (113, 119, 120), start, end)

    def _sign(self, text, color):
        key = (text, color)
        if key not in self.signs:
            label = self.font.render(text, True, color)
            plate = pygame.Surface((label.get_width() + 8, label.get_height() + 1), pygame.SRCALPHA)
            plate.fill(INK)
            pygame.draw.line(plate, color, (0, 0), (0, plate.get_height()), 2)
            plate.blit(label, (4, -1))
            self.signs[key] = plate
        return self.signs[key]

    def _mark_vertices(self, surface, race):
        human = race.racers[0]
        checkpoints = race.circuit.checkpoints
        next_id = checkpoints[human.next_checkpoint] if human.next_checkpoint < len(checkpoints) else race.circuit.start
        for vertex in race.circuit.graph.vertices.values():
            point = self.positions[vertex.id]
            if vertex.kind == "checkpoint":
                color, text = WHITE, str(vertex.checkpoint_order)
            elif vertex.kind in {"nitro", "fuel"}:
                color = FUEL if vertex.kind == "fuel" else NITRO
                text = ("F" if vertex.kind == "fuel" else "N") + str(vertex.id)
            elif vertex.id == race.circuit.start:
                color, text = WHITE, "S/F"
            else:
                pygame.draw.circle(surface, (180, 186, 181), point, 3, 1)
                continue
            if vertex.id == next_id and not human.finished and not human.dnf:
                color = SUGGESTED
                pygame.draw.ellipse(surface, color, (point.x - 14, point.y - 7, 28, 14), 2)
                # Two illuminated bollards mark the next timing loop.
                for side in (-1, 1):
                    foot = point + (side * 13, side * 3)
                    pygame.draw.line(surface, INK, foot, foot + (0, -9), 4)
                    pygame.draw.line(surface, SUGGESTED, foot + (0, -10), foot + (0, -8), 3)
            pole = point + (8, -12)
            pygame.draw.line(surface, INK, point + (4, -2), pole, 2)
            plate = self._sign(text, color)
            position = (pole.x, pole.y - plate.get_height() + 2)
            surface.blit(plate, position)
            if vertex.kind in {"nitro", "fuel"} and not race.service_active[vertex.id]:
                pygame.draw.line(surface, HAZARD, (pole.x, pole.y),
                                 (pole.x + plate.get_width(), position[1]), 2)

    def draw(self, surface, race, suggested, selected_edge, colors, motion=True):
        surface.blit(self.base, (0, 0))
        draw_atmosphere(surface, race.circuit.name, race.elapsed if motion else 0)
        suggested = set(suggested)
        for edge in race.circuit.graph.edges.values():
            road = self.roads[edge.id]
            if edge.id in suggested:
                pygame.draw.lines(surface, SUGGESTED, False, road.points, 3)
            if edge.id == selected_edge:
                pygame.draw.lines(surface, SELECTED, False, road.points, 4)
                t = (.25 + race.elapsed * .7) % 1 if motion else .5
                if race.racers[0].vertex == edge.target:
                    t = 1 - t
                point, _ = road.sample(t)
                pygame.draw.circle(surface, WHITE, point, 3)
            if edge.directed:
                point, direction = road.sample(.35)
                normal = Vector2(-direction.y, direction.x)
                tip = point + direction * 6
                pygame.draw.polygon(surface, WHITE, (tip, point - direction * 4 + normal * 4,
                                                      point - direction * 4 - normal * 4))
            point, direction = road.sample(.58)
            if edge.status == "blocked":
                pygame.draw.circle(surface, INK, point, 9)
                for side in (-1, 1):
                    pygame.draw.line(surface, HAZARD, point + (-5, side * 5), point + (5, -side * 5), 3)
            elif edge.status == "restricted" or edge.obstacle:
                diamond = [point + d for d in ((0, -7), (7, 0), (0, 7), (-7, 0))]
                pygame.draw.polygon(surface, INK, diamond)
                pygame.draw.polygon(surface, HAZARD, diamond, 2)
                if edge.status == "restricted":
                    pygame.draw.line(surface, HAZARD, point + (-3, 0), point + (3, 0), 2)
        self._mark_vertices(surface, race)
        # Draw near cars last. Small grid/lane offsets separate racers occupying
        # the same section of road; longitudinal progress remains engine-owned.
        cars = []
        for order, racer in enumerate(race.racers):
            pos = self.positions[racer.vertex]
            heading = Vector2(1, 0)
            if racer.edge_id is not None:
                edge = race.circuit.graph.edges[racer.edge_id]
                reverse = racer.vertex != edge.source
                t = 1 - racer.edge_progress if reverse else racer.edge_progress
                pos, heading = self.roads[edge.id].sample(t)
                if reverse:
                    heading = -heading
                # When cars run abreast, keep the whole pack distinguishable
                # without moving a lone car away from its road centreline.
                lane = 0.0
                for i, other in enumerate(race.racers):
                    if other.edge_id == racer.edge_id and other.vertex == racer.vertex:
                        gap = abs(other.edge_progress - racer.edge_progress)
                        lane += ((order > i) - (order < i)) * max(0, 1 - gap / .10)
                pos += Vector2(-heading.y, heading.x) * lane * 4.0
            else:
                pos = pos + ((order % 2) * 12 - 6, (order // 2) * 9 - 4)
            cars.append((pos.y, order, pos, heading, racer))
        for _, order, pos, heading, racer in sorted(cars):
            _car(surface, pos, heading, colors[racer.id % len(colors)],
                 racer.nitro_remaining > 0 and racer.edge_id is not None, order == 0)
