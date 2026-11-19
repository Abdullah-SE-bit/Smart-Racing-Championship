"""Quick Race presentation, input isolation and simulation timing."""

import os
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from smart_racing.ui.app import App


@pytest.fixture
def app():
    instance = App()
    yield instance
    pygame.quit()


def click(app, position):
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position))


@pytest.mark.parametrize("entry", ["menu", "planner"])
@pytest.mark.parametrize("skip", ["enter", "click"])
def test_quick_grid_entry_and_skip_consume_activation(app, entry, skip):
    if entry == "menu":
        app.draw_menu()
        click(app, (230, 427))
    else:
        app.open_quick_planner()
        app.draw_planner()
        click(app, (1050, 690))
    assert app.screen == "race" and app.quick_grid_started is not None
    app.draw_race()
    player = app.race.racers[0]
    if skip == "enter":
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
    else:
        click(app, (470, 775))  # Drive's position in the live race.
    assert app.quick_grid_started is None and app.screen == "race"
    assert player.edge_id is None and app.race.elapsed == 0


def test_grid_countdown_freezes_simulation_until_release(app, monkeypatch):
    app.start_quick_race()
    start = app.time
    frames = []
    monkeypatch.setattr(app, "start_intro", lambda: None)
    app.clock = SimpleNamespace(tick=lambda fps: 100)

    def record_frame():
        frames.append((app.time - start, app.race.elapsed, app.quick_grid_started))
        if len(frames) == 26:
            app.running = False

    monkeypatch.setattr(app, "present", record_frame)
    app.run()
    for moment, elapsed, grid in frames:
        if moment < 2.4 - 1e-9:
            assert elapsed == 0 and grid is not None
    assert frames[-1][1] > 0 and frames[-1][2] is None


def test_reduced_motion_and_championship_go_directly_to_race(app):
    app.reduced_motion = True
    app.draw_menu()
    click(app, (230, 427))
    assert app.screen == "race" and app.quick_grid_started is None
    app.reduced_motion = False
    app.prepare_championship()
    app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    app.draw_planner()
    click(app, (1050, 690))
    assert app.championship and app.screen == "race" and app.quick_grid_started is None
