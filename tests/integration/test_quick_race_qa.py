"""Quick Race UI and rules quality assurance checks."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from smart_racing.ui.app import App
from smart_racing.tracks.circuits import load_circuit


@pytest.fixture
def app():
    instance = App()
    instance.reduced_motion = True
    yield instance
    pygame.quit()


def draw_race_controls(app):
    app.quick_grid_started = None
    app.buttons = []
    app.draw_race()


def click_race_control(app, point):
    draw_race_controls(app)
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))


def test_quick_race_menu_entry_uses_each_selected_authored_circuit(app):
    for track_index, path in enumerate(app.authored_paths):
        app.circuit = load_circuit(path)
        app.track_index = track_index
        app.buttons = []
        app.draw_menu()
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(230, 427)))
        assert app.screen == "race"
        assert app.race.circuit.name == app.circuit.name
        assert len(app.race.racers) >= 4
        assert app.race.racers[0].fuel == 100
        assert app.quick_grid_started is None  # Reduced motion starts immediately.
        app.go("menu")


def test_race_camera_button_toggles_views_without_changing_race_state(app):
    app.start_quick_race()
    before = (app.race.elapsed, [(r.vertex, r.fuel, r.nitro) for r in app.race.racers])
    assert app.overhead_camera
    click_race_control(app, (916, 125))
    assert not app.overhead_camera
    click_race_control(app, (916, 125))
    assert app.overhead_camera
    assert (app.race.elapsed, [(r.vertex, r.fuel, r.nitro) for r in app.race.racers]) == before


def test_previous_next_and_drive_buttons_cover_road_choice_boundaries(app):
    app.start_quick_race()
    racer = app.race.racers[0]
    junction = next(vertex for vertex in sorted(app.race.circuit.graph.vertices)
                    if len(list(app.race.circuit.graph.neighbors(vertex))) >= 2)
    racer.vertex = junction
    racer.edge_id = None
    racer.desired_target = None
    racer.desired_edge_id = None
    racer.visited_since_checkpoint = {junction}
    options = app.race.options(racer)
    app.selected_road = 0

    click_race_control(app, (122, 776))  # Previous from index zero wraps to the last road.
    assert app.selected_road == -1
    click_race_control(app, (470, 776))  # Drive uses the wrapped, last road.
    assert racer.desired_target == options[-1][0]
    assert racer.desired_edge_id == options[-1][1].id

    racer.edge_id = None
    racer.desired_target = None
    racer.desired_edge_id = None
    app.selected_road = 0
    click_race_control(app, (297, 776))
    assert app.selected_road == 1
    click_race_control(app, (470, 776))
    assert racer.desired_target == options[1][0]
    assert racer.desired_edge_id == options[1][1].id


@pytest.mark.parametrize(("starting_nitro", "expected_nitro", "accepted"),
                         [(0, 0, False), (1, 0, True), (3, 2, True)])
def test_boost_button_respects_empty_single_and_maximum_charge_boundaries(
        app, starting_nitro, expected_nitro, accepted):
    app.start_quick_race()
    racer = app.race.racers[0]
    racer.nitro = starting_nitro
    click_race_control(app, (647, 776))
    assert racer.nitro == expected_nitro
    assert (racer.nitro_remaining > 0) is accepted


@pytest.mark.parametrize(("fuel", "expected"), [(0, 40), (60, 100), (99, 100), (100, 100)])
def test_refuel_button_respects_fuel_boundaries_and_one_stop_per_visit(app, fuel, expected):
    app.start_quick_race()
    racer = app.race.racers[0]
    station = next(vertex.id for vertex in app.race.circuit.graph.vertices.values()
                   if vertex.kind == "fuel")
    racer.vertex = station
    racer.edge_id = None
    racer.fuel = fuel
    click_race_control(app, (822, 776))
    assert racer.fuel == expected
    if fuel < 100:
        assert racer.refuelled_here
        assert racer.stop_remaining == 3.0
        click_race_control(app, (822, 776))
        assert racer.fuel == expected


def test_refuel_button_has_no_effect_away_from_station(app):
    app.start_quick_race()
    racer = app.race.racers[0]
    racer.fuel = 55
    click_race_control(app, (822, 776))
    assert racer.fuel == 55
    assert not racer.refuelled_here


def test_pause_resume_and_main_menu_buttons_return_expected_states(app):
    app.start_quick_race()
    click_race_control(app, (1005, 776))
    assert app.paused
    click_race_control(app, (1005, 776))
    assert not app.paused

    click_race_control(app, (1135, 125))
    assert app.screen == "menu"
    assert app.race is not None


def test_results_button_appears_only_after_race_ends_and_opens_classification(app):
    app.start_quick_race()
    app.race.elapsed = app.race.time_limit
    app.buttons = []
    app.draw_race()
    results_button = next(rect for rect, _action in app.buttons if rect.topleft == (885, 460))
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=results_button.center))
    assert app.screen == "dashboard"
