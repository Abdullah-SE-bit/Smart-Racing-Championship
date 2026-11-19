"""Championship presentation must respect input, motion and scoring."""

import os

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


def skip(app, method):
    if method == "enter":
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0)
    else:
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1050, 690))
    app.event(event)


@pytest.mark.parametrize("method", ["enter", "click"])
def test_championship_opener_and_results_consume_skip(app, method):
    app.prepare_championship()
    assert app.screen == "planner" and app.title_opener_started is not None
    app.draw_planner()
    skip(app, method)
    assert app.title_opener_started is None and app.screen == "planner"
    assert app.race is None

    app.start_planned_race()
    app.race.elapsed = app.race.time_limit
    winner = app.race.racers[2]
    winner.finished = True
    winner.finish_time = 35.0
    app.finish_race()
    assert app.screen == "dashboard" and app.title_reveal_started is not None
    assert app.entries[2].total_points == 25
    app.draw_dashboard()
    skip(app, method)
    assert app.title_reveal_started is None and app.screen == "dashboard"
    app.finish_race()
    assert app.entries[2].total_points == 25 and app.entries[2].wins == 1
    app.next_championship_race()
    assert app.screen == "planner" and app.track_index == 1
    assert app.entries[2].total_points == 25


def test_reduced_motion_reaches_final_standings_without_timed_overlays(app):
    app.reduced_motion = True
    app.prepare_championship()
    for index in range(len(app.authored_paths)):
        assert app.track_index == index and app.title_opener_started is None
        app.draw_planner()
        app.start_planned_race()
        app.race.elapsed = app.race.time_limit
        app.finish_race()
        assert app.screen == "dashboard" and app.title_reveal_started is None
        app.draw_dashboard()
        app.next_championship_race()
    assert app.screen == "menu" and not app.pending_championship
