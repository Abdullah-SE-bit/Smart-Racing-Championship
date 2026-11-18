"""Verify the new race camera follows the live graph in the actual game screen."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from smart_racing.events.queue import Event
from smart_racing.ui.app import App


def test_live_closure_and_expiration_reach_both_race_views():
    app = App()
    try:
        app.start_race()
        app.reduced_motion = True
        app.draw_race()
        race = app.race
        human = race.racers[0]
        road = race.options(human)[0][1]
        assert road.id in app._race_route.edges
        point, _ = app.race_scene.roads[road.id].sample(.58)
        marker = pygame.Rect(42 + int(point.x) - 8, 222 + int(point.y) - 8, 17, 17)

        def pixels():
            return pygame.image.tobytes(app.surface.subsurface(marker), "RGB")

        opened = pixels()
        race.schedule(Event(700, .1, 1, "block", road.id, .3))
        race.tick(.1)
        app.draw_race()
        assert road.status == "blocked" and road.id not in app._race_route.edges
        assert pixels() != opened

        # The visible camera button goes through the same input path as a real
        # click. Both views continue the same race while the event expires.
        click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(900, 124))
        app.event(click)
        app.buttons = []
        app.draw_race()
        assert not app.overhead_camera and road.id not in app._race_route.edges
        race.tick(.4)
        app.draw_race()
        assert road.status == "open" and road.id in app._race_route.edges
        app.event(click)
        app.draw_race()
        assert app.overhead_camera and app.race is race
        assert race.elapsed == .5
    finally:
        pygame.quit()
