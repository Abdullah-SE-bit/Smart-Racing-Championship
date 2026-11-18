"""Finish-line broadcast, rendered from the current race and its results."""

from math import cos, isfinite, sin

import pygame

from smart_racing.championship.standings import standings
from smart_racing.ui.visualization.telemetry import BLUE, RED, SILVER, WHITE


def _chequered_flag(surface, area, time):
    """A folded strip of flag fabric projected onto the winner panel."""
    patch = surface.subsurface(area)
    cols, rows = 12, 5
    points = []
    for row in range(rows + 1):
        line = []
        for col in range(cols + 1):
            u, v = col / cols, row / rows
            wave = sin(8 * u - time) * (9 + 17 * u)
            x = 12 + u * (area.width - 20) - 18 * v
            y = 42 + 83 * v + 16 * cos(4 * u) + wave - 20 * u
            line.append((round(x), round(y)))
        points.append(line)
    for row in range(rows):
        for col in range(cols):
            light = round(30 * cos(8 * (col + .5) / cols - time))
            base = 177 + light if (row + col) % 2 == 0 else 54 + light // 3
            pygame.draw.polygon(patch, (base, base + 4, base + 8),
                                (points[row][col], points[row][col + 1],
                                 points[row + 1][col + 1], points[row + 1][col]))


def draw_classification(app, colors):
    race = app.race
    field = race.results()
    winner = field[0] if field and field[0].finished else None
    app.header("Classification", "Race results", race.circuit.name)
    app.nav()
    app.card((40, 220, 770, 370))
    for title, x in (("POS", 72), ("DRIVER", 150), ("FINISH TIME", 373),
                     ("BEST LAP", 534), ("RACE PTS", 676)):
        app.label(title, x, 246, 14, SILVER)
    points = {r.racer_id: r.points_awarded for r in race.result_records(app.track_index + 1)}
    for index, racer in enumerate(field):
        y = 288 + index * 70
        pygame.draw.rect(app.surface, (34, 41, 50) if racer.id == 0 else (26, 31, 39),
                         (62, y - 6, 727, 58))
        color = colors[racer.id % len(colors)]
        pygame.draw.rect(app.surface, color, (62, y - 6, 4, 58))
        app.label(f"{index + 1:02}", 77, y, 30, color)
        app.label(racer.name, 150, y + 5, 24, WHITE)
        app.label(f"{racer.finish_time:.2f}s" if racer.finished else "DNF", 373, y + 7, 20, WHITE)
        app.label(f"{racer.fastest_lap:.2f}s" if isfinite(racer.fastest_lap) else "—", 534, y + 7, 20, WHITE)
        app.label(f"+{points[racer.id]}" if app.championship else "—", 689, y + 7, 20, SILVER)
    app.card((832, 220, 408, 370), (29, 35, 43))
    _chequered_flag(app.surface, pygame.Rect(842, 243, 388, 168),
                    0 if app.reduced_motion else app.time * 2)
    app.label("RACE WINNER" if winner else "RACE CLOSED", 861, 414, 16, RED)
    app.label(winner.name if winner else "NO FINISHERS", 858, 435, 42, WHITE)
    finished = sum(r.finished for r in field)
    app.label(f"{finished} OF {len(field)} FINISHED", 861, 530, 18, SILVER)
    app.card((40, 610, 1200, 100))
    if app.championship:
        leader = standings(app.entries)[0]
        final = app.track_index + 1 == len(app.authored_paths)
        app.label("SEASON CHAMPION" if final else "CHAMPIONSHIP LEADER", 65, 625, 14, RED)
        app.label(f"{leader.name}   /   {leader.total_points} PTS", 65, 649, 24, WHITE)
        app.menu_button((680, 625, 190, 56), "STANDINGS", None, lambda: app.go("standings"))
        app.menu_button((900, 625, 280, 56), "FINISH CHAMPIONSHIP" if final else "NEXT RACE",
                        None, app.next_championship_race, True)
    else:
        app.label("QUICK RACE", 65, 642, 20, BLUE)
        app.menu_button((900, 625, 280, 56), "RACE AGAIN", None, lambda: app.start_race(False), True)
