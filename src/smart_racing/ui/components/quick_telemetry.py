"""Quick Race broadcast strip, drawn from the four cars' checkpoint records."""

import math

import pygame


def draw_quick_telemetry(app):
    """Show the field's race distance in the space beneath the camera controls."""
    race = app.race
    checkpoints = race.circuit.checkpoints
    if not checkpoints:
        return
    surface = app.surface
    driver = race.racers[0]
    if (app.overhead_camera and not app.reduced_motion and driver.edge_id is not None
            and driver.nitro_remaining > 0):
        # Keep the centre of the driving view clear while boost is active.
        view = surface.subsurface((42, 222, 796, 455))
        for ray in range(24):
            angle = math.tau * ray / 24
            phase = (race.elapsed * 2.8 + ray * .618) % 1
            radius = .79 + .46 * phase
            x, y = 398 * math.cos(angle), 228 * math.sin(angle)
            pygame.draw.aaline(view, (128, 199, 226),
                               (398 + x * radius, 228 + y * radius),
                               (398 + x * (radius + .1), 228 + y * (radius + .1)))
    ink = (222, 231, 239)
    chassis = (15, 21, 29)
    colors = ((115, 196, 239), (245, 84, 79), (255, 180, 113), (185, 170, 235))
    pygame.draw.polygon(surface, chassis, ((806, 160), (1230, 160), (1230, 196),
                                            (1218, 208), (806, 208)))
    pygame.draw.line(surface, (69, 82, 98), (806, 160), (1229, 160))
    app.label("FIELD", 818, 166, 16, ink)
    app.label("PROGRESS", 818, 185, 12, (164, 180, 198))
    left, right = 902, 1208
    lap_units = len(checkpoints) + 1  # Crossing the finish line completes the lap.
    for index, racer in enumerate(race.racers[:4]):
        units = racer.laps * lap_units + racer.next_checkpoint
        destination = (checkpoints[racer.next_checkpoint] if racer.next_checkpoint < len(checkpoints)
                       else race.circuit.start)
        if racer.edge_target == destination:
            units += racer.edge_progress
        progress = 1.0 if racer.finished else min(1.0, units / (race.laps_required * lap_units))
        x = left + round((right - left) * progress)
        y = 169 + 9 * index
        color = colors[racer.id % len(colors)] if not racer.dnf else (115, 117, 120)
        pygame.draw.line(surface, (48, 59, 72), (left, y), (right, y))
        pygame.draw.line(surface, color, (left, y), (x, y), 2)
        pygame.draw.polygon(surface, color, ((x - 3, y - 3), (x + 4, y), (x - 3, y + 3)))
        if racer.nitro_remaining > 0 and not app.reduced_motion:
            trail = 5 + int(race.elapsed * 30) % 8
            pygame.draw.line(surface, ink, (max(left - 12, x - trail), y), (x - 3, y))
