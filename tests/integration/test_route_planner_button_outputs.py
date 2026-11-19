"""Expected outputs for every button in the planner and its route tools."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from smart_racing.algorithms.routing.shortest import shortest_path
from smart_racing.core.graph import Edge, Graph, Vertex
from smart_racing.tracks.circuits import load_circuit
from smart_racing.ui.app import App, PROFILES


@pytest.fixture
def app():
    instance = App()
    instance.reduced_motion = True
    yield instance
    pygame.quit()


def click_planner(app, point):
    app.time = app.planner_entered + 1.0
    app.buttons = []
    app.draw_planner()
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))


@pytest.mark.parametrize(
    ("profile_index", "point"),
    ((0, (965, 548)), (1, (1136, 548)),
     (2, (965, 587)), (3, (1136, 587))),
    ids=("balanced", "speed", "economy", "safety"),
)
def test_each_profile_chip_selects_its_route_and_cost(app, profile_index, point):
    app.go("planner")
    click_planner(app, point)

    profile_name = list(PROFILES)[profile_index]
    assert app.profile_index == profile_index
    route = app.planned_route(PROFILES[profile_name])
    expected = shortest_path(app.circuit.graph, app.source, app.target,
                             PROFILES[profile_name], app.route_algorithm)
    assert app.screen == "planner"
    assert route.vertices == expected.vertices
    assert route.edges == expected.edges
    assert route.cost == pytest.approx(expected.cost)


def test_planner_navigation_and_route_mode_buttons(app):
    app.go("planner")
    click_planner(app, (915, 181))
    assert app.screen == "planner" and app.ordered_plan
    lap = app.planned_route(PROFILES["Balanced"])
    assert lap.vertices[0] == app.source
    assert lap.vertices[-1] == app.circuit.start
    assert [lap.vertices.index(v) for v in app.ordered_destinations()[:-1]] == sorted(
        lap.vertices.index(v) for v in app.ordered_destinations()[:-1])

    click_planner(app, (915, 181))
    assert not app.ordered_plan
    assert app.planned_route(PROFILES["Balanced"]).vertices[-1] == app.target

    click_planner(app, (1135, 125))
    assert app.screen == "menu"


def test_compare_button_shows_four_costed_routes_and_returns_to_planner(app, monkeypatch):
    app.go("planner")
    click_planner(app, (720, 181))
    assert app.screen == "compare"

    labels = []
    monkeypatch.setattr(app, "label", lambda value, *args, **kwargs: labels.append(str(value)))
    app.buttons = []
    app.draw_comparison()
    assert all(name in labels for name in PROFILES)
    assert "COST" in labels
    assert any("FROM" in value and "TO" in value for value in labels)

    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1040, 700)))
    assert app.screen == "planner"


def test_algorithm_button_switches_both_ways_without_changing_optimal_cost(app):
    app.go("planner")
    before = app.planned_route(PROFILES["Balanced"])
    click_planner(app, (965, 635))
    assert app.route_algorithm == "astar"
    astar = app.planned_route(PROFILES["Balanced"])
    assert astar.cost == pytest.approx(before.cost)

    click_planner(app, (965, 635))
    assert app.route_algorithm == "dijkstra"
    assert app.planned_route(PROFILES["Balanced"]).cost == pytest.approx(before.cost)


def test_resource_buttons_show_real_outputs_and_return_to_planner(app, monkeypatch):
    app.go("planner")
    expected_route, expected_stops = app.refuel_stops()
    click_planner(app, (177, 683))
    assert app.screen == "refuel"
    assert app.refuel_page == 0
    assert app.refuel_stops() == (expected_route, expected_stops)

    labels = []
    monkeypatch.setattr(app, "label", lambda value, *args, **kwargs: labels.append(str(value)))
    app.buttons = []
    app.draw_refuel_plan()
    assert any("SELECTED ROUTE" in value for value in labels)
    if expected_stops:
        assert any("STOP(S)" in value for value in labels)
        assert all(str(vertex) in " ".join(labels) for vertex, _amount in expected_stops)
    else:
        assert any("No refuelling stops" in value or "No feasible fuel plan" in value
                   for value in labels)
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1040, 690)))
    assert app.screen == "planner"


def test_refuel_next_and_previous_buttons_paginate_a_real_multi_stop_route(app):
    graph = Graph()
    for vertex_id in range(10):
        kind = "start" if vertex_id == 0 else "finish" if vertex_id == 9 else "fuel"
        graph.add_vertex(Vertex(vertex_id, vertex_id * 50, 250, kind))
    for edge_id in range(9):
        graph.add_edge(Edge(edge_id, edge_id, edge_id + 1, 40, 1, 40))
    app.circuit.graph = graph
    app.source, app.target = 0, 9
    app._planner_key = None
    app.open_refuel_plan()

    route, stops = app.refuel_stops()
    assert route.vertices == list(range(10))
    assert stops is not None and len(stops) > 6
    app.buttons = []
    app.draw_refuel_plan()
    assert app.refuel_page == 0
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(365, 612)))
    assert app.refuel_page == 1

    labels = []
    app.buttons = []
    app.label = lambda value, *args, **kwargs: labels.append(str(value))
    app.draw_refuel_plan()
    assert any("PAGE 2 OF 2" in value for value in labels)
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(165, 612)))
    assert app.refuel_page == 0


def test_alternatives_next_previous_and_back_controls(app):
    app.go("planner")
    app.source, app.target = 0, 4
    click_planner(app, (394, 683))
    assert app.screen == "alternatives"
    assert app.alternative_paths
    assert len(app.alternative_paths) > 1
    expected = [path[:] for path in app.alternative_paths]
    assert all(path[0] == 0 and path[-1] == 4 for path in expected)

    app.buttons = []
    app.draw_alternatives()
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1135, 504)))
    assert app.alternative_index == 1 % len(expected)
    app.buttons = []
    app.draw_alternatives()
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(963, 504)))
    assert app.alternative_index == 0
    app.buttons = []
    app.draw_alternatives()
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1050, 681)))
    assert app.screen == "planner"


def test_new_circuit_button_creates_a_valid_seeded_workshop_result(app):
    app.go("planner")
    click_planner(app, (1135, 635))
    assert app.screen == "generation"
    assert app.circuit.name == "Generated 1000"
    assert app.generation_trace[-1]["stage"] == "accepted"
    assert len(app.circuit.checkpoints) == 10
    assert app.source == app.circuit.start
    assert app.target in app.circuit.checkpoints

    app.buttons = []
    app.draw_generation()
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1050, 712)))
    assert app.screen == "planner"


def test_season_order_control_rejects_regeneration_and_starts_championship(app):
    app.prepare_championship()
    original_track = app.circuit.name
    click_planner(app, (1135, 635))
    assert app.screen == "planner"
    assert app.circuit.name == original_track
    assert "fixed season order" in app.validation_message

    click_planner(app, (1050, 691))
    assert app.screen == "race"
    assert app.championship and not app.pending_championship
    assert app.race.circuit.name == original_track
    assert len(app.entries) == 4
    assert app.race.racers[0].vertex == app.circuit.start


def test_quick_race_button_starts_the_selected_circuit(app):
    app.go("planner")
    app.source, app.target = 0, 4
    planned_name = app.circuit.name
    click_planner(app, (1050, 691))
    assert app.screen == "race"
    assert app.race is not None
    assert app.race.circuit.name == planned_name
    assert len(app.race.racers) >= 4
    assert app.race.racers[0].vertex == app.circuit.start


def test_comparison_save_and_invalid_track_buttons_report_expected_results(app, tmp_path):
    app.go("planner")
    app.saved_directory = tmp_path
    click_planner(app, (720, 181))
    original_name = app.circuit.name
    before_graph = dict(app.circuit.graph.edges)
    app.buttons = []
    app.draw_comparison()
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(202, 700)))
    assert app.validation_message.startswith("Rejected:")
    assert app.circuit.name == original_name
    assert app.circuit.graph.edges == before_graph

    app.buttons = []
    app.draw_comparison()
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(478, 700)))
    saved = list(tmp_path.glob("*.json"))
    assert len(saved) == 1
    assert app.validation_message.startswith("Saved:")
    assert saved[0] in app.circuit_paths
    assert load_circuit(saved[0]).graph.edges == app.circuit.graph.edges
