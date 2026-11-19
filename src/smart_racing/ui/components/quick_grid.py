"""Pre-race grid broadcast. Elapsed time belongs to the presentation clock."""

import pygame

from smart_racing.ui.components.broadcast import draw_circuit_model, ease_out


GRID_DURATION = 2.4


def draw_grid(app, elapsed):
    surface = app.surface
    app.draw_pit_background()
    ink = (248, 245, 240)
    red = (238, 54, 60)
    dark = (13, 17, 23)
    # The lower third travels in as one plate, leaving the venue visible above.
    lift = round(180 * (1 - ease_out(elapsed / .42)))
    top = 470 + lift
    pygame.draw.polygon(surface, dark, [(0, top), (775, top), (832, top - 52),
                                        (1280, top - 52), (1280, 800), (0, 800)])
    pygame.draw.lines(surface, red, False, [(0, top), (775, top), (832, top - 52),
                                            (1280, top - 52)], 3)
    app.label("QUICK RACE", 52, top + 32, 20, red)
    title = app.broadcast.title[104].render(app.circuit.name.upper(), True, ink)
    if title.get_width() > 690:
        title = pygame.transform.smoothscale_by(title, 690 / title.get_width())
    surface.blit(title, title.get_rect(midleft=(48, top + 125)))
    app.label(f"{app.laps_setting} LAPS     /     {len(app.race.racers)} DRIVERS",
              54, top + 208, 24, ink)
    model = pygame.Surface((748, 388))
    model.fill(dark)
    draw_circuit_model(model, model.get_rect(), app.circuit, elapsed)
    surface.blit(pygame.transform.smoothscale(model, (374, 194)), (838, top + 8))
    # Five lamps charge in sequence, then go dark together for lights out.
    release = elapsed >= 2.05
    y = 150 - round(80 * (1 - ease_out(elapsed / .26)))
    pygame.draw.line(surface, (55, 63, 72), (0, y + 20), (1280, y + 20), 3)
    pygame.draw.rect(surface, dark, (450, y - 14, 380, 70), border_radius=12)
    for index in range(5):
        x = 500 + index * 70
        on = not release and elapsed >= .25 + index * .33
        for radius, color in ((25, (54, 60, 68)), (22, (36, 42, 50)),
                              (19, (233, 44, 55) if on else (64, 39, 44))):
            pygame.draw.circle(surface, color, (x, y + 20), radius)
        if on:
            pygame.draw.circle(surface, (255, 169, 145), (x - 5, y + 14), 5)
    app.label("LIGHTS OUT" if release else "STARTING GRID", 54, top + 264, 20, ink)
    app.label("Enter or click to skip", 1020, top + 264, 16, (184, 195, 203))
