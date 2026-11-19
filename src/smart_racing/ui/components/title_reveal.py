"""Championship points and position changes after a classified round."""

import pygame

from smart_racing.ui.components.broadcast import INK, RED, ease_out


REVEAL_DURATION = 3.6
SETTLED_AT = 2.45


def draw_title_reveal(app, elapsed, before, after):
    """Render two ordered snapshots without modifying the championship."""
    app.draw_pit_background()
    surface = app.surface
    if not after:
        return
    old = {entry.racer_id: (rank, entry.total_points) for rank, entry in enumerate(before)}
    count = ease_out((elapsed - .45) / 1.15)
    move = ease_out((elapsed - 1.65) / .8)
    final = app.track_index + 1 == len(app.authored_paths)
    settled = elapsed >= SETTLED_AT
    muted = (174, 186, 197)
    accent = RED if settled else muted
    pygame.draw.polygon(surface, (17, 21, 29), [(0, 182), (546, 182), (594, 230),
                                                 (594, 697), (0, 697)])
    pygame.draw.line(surface, accent, (50, 276), (132, 276), 4)
    app.label(f"ROUND {app.track_index + 1}  /  {app.circuit.name.upper()}", 50, 217, 20, muted)
    app.label(("SEASON CHAMPION" if final else "CHAMPIONSHIP LEADER")
              if settled else "CHAMPIONSHIP STANDINGS", 50, 310, 24, accent)
    headline = after[0].name if settled else "TITLE RACE"
    title = app.broadcast.title[104].render(headline.upper(), True, INK)
    if title.get_width() > 500:
        title = pygame.transform.smoothscale_by(title, 500 / title.get_width())
    surface.blit(title, (46, 355))
    if settled:
        leader = after[0]
        wins = "WIN" if leader.wins == 1 else "WINS"
        app.label(f"{leader.total_points} POINTS    /    {leader.wins} {wins}", 52, 518, 30, INK)
    else:
        app.label("Round points" if elapsed < 1.65 else "Positions updated", 52, 518, 24, muted)

    app.label("POSITION", 624, 211, 16, INK)
    app.label("ROUND", 994, 211, 16, INK)
    app.label("TOTAL", 1127, 211, 16, INK)
    tallest = max(1, max(entry.total_points for entry in after))
    for rank, entry in enumerate(after):
        start_rank, previous = old.get(entry.racer_id, (rank, 0))
        earned = entry.total_points - previous
        y = 251 + round((start_rank + (rank - start_rank) * move) * 91)
        score = previous + round(count * earned)
        pygame.draw.rect(surface, (26, 32, 41), (621, y, 603, 78), border_radius=4)
        strip = accent if rank == 0 and settled else muted
        pygame.draw.rect(surface, strip, (621, y, 4, 78))
        app.label(f"{(rank if settled else start_rank) + 1:02}", 641, y + 15, 30, muted)
        app.label(entry.name.upper(), 714, y + 15, 30, INK)
        app.label(f"+{score - previous}", 996, y + 19, 24, strip)
        app.label(str(score), 1130, y + 15, 30, INK)
        pygame.draw.rect(surface, (53, 64, 77), (715, y + 60, 244, 3))
        pygame.draw.rect(surface, strip, (715, y + 60, round(244 * score / tallest), 3))
    app.label("Enter or click to continue", 50, 735, 16, INK)
