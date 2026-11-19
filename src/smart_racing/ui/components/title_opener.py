"""Championship round opener drawn from the current venue and points table."""

import pygame

from smart_racing.championship.standings import standings
from smart_racing.ui.components.broadcast import ease_out


TITLE_DURATION = 2.6
IVORY = (244, 239, 227)
RED = (230, 49, 56)
CARBON = (18, 19, 22)


def draw_title_opener(app, elapsed):
    app.draw_pit_background()
    surface = app.surface
    round_number = app.track_index + 1
    rounds = len(app.authored_paths)
    order = standings(app.entries)
    if round_number == 1:
        story = f"{len(order)} drivers start level on points."
    elif len(order) >= 2:
        leader, second = order[:2]
        gap = leader.total_points - second.total_points
        if gap:
            story = f"{leader.name} leads {second.name} by {gap} {'point' if gap == 1 else 'points'}."
        else:
            story = f"{leader.name} and {second.name} are level on {leader.total_points} points."
    else:
        story = "Final round" if round_number == rounds else "Championship round"

    # The venue stays visible through the opening between the two plates.
    top = 476 + round(170 * (1 - ease_out(elapsed / .42)))
    pygame.draw.polygon(surface, CARBON, [(0, top), (878, top), (938, top - 48),
                                          (1280, top - 48), (1280, 800), (0, 800)])
    pygame.draw.lines(surface, RED, False, [(0, top), (878, top), (938, top - 48),
                                            (1280, top - 48)], 3)
    x = 54 - round(82 * (1 - ease_out((elapsed - .08) / .44)))
    app.label("THE TITLE FIGHT", x, top + 30, 24, RED)
    title = app.broadcast.title[104].render(app.circuit.name.upper(), True, IVORY)
    if title.get_width() > 822:
        title = pygame.transform.smoothscale_by(title, 822 / title.get_width())
    surface.blit(title, title.get_rect(midleft=(x - 4, top + 125)))
    app.label(story, x, top + 208, 24, IVORY)

    app.label("ROUND", 980, top + 15, 20, IVORY)
    number = app.broadcast.title[104].render(f"{round_number:02}", True, IVORY)
    surface.blit(number, (970, top + 34))
    app.label(f"/ {rounds:02}", 1090, top + 96, 30, RED)
    for index in range(rounds):
        left = 982 + index * 52
        pygame.draw.rect(surface, RED if index <= app.track_index else (76, 77, 79),
                         (left, top + 176, 44, 5))
    app.label("Enter or click to skip", 980, top + 252, 16, IVORY)
