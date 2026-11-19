"""Risk-focused quality checks for the route planner and its controls."""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from smart_racing.algorithms.routing.shortest import shortest_path
from smart_racing.tracks.circuits import load_circuit
from smart_racing.ui.app import App, PROFILES


@pytest.fixture
def app():
    instance = App()
    yield instance
    pygame.quit()


def test_all_authored_track_routes_match_between_algorithms_and_edge_costs(app):
    """Exercise all source/target pairs, presets, and both routing algorithms."""
    for track_index in range(len(app.authored_paths)):
        app.track_index = track_index
        app.circuit = load_circuit(app.authored_paths[track_index])
        graph = app.circuit.graph
        vertices = sorted(graph.vertices)
        for source in vertices:
            for target in vertices:
                for profile in PROFILES.values():
                    dijkstra = shortest_path(graph, source, target, profile, "dijkstra")
                    astar = shortest_path(graph, source, target, profile, "astar")
                    assert astar.cost == pytest.approx(dijkstra.cost)
                    for route in (dijkstra, astar):
                        if not route.vertices:
                            assert route.cost == float("inf")
                            assert route.edges == []
                            continue
                        assert route.vertices[0] == source
                        assert route.vertices[-1] == target
                        assert len(route.edges) + 1 == len(route.vertices)
                        assert sum(profile.cost(graph.edges[edge_id])
                                   for edge_id in route.edges) == pytest.approx(route.cost)
                        for origin, destination, edge_id in zip(
                                route.vertices, route.vertices[1:], route.edges):
                            assert any(neighbor == destination and road.id == edge_id
                                       for neighbor, road in graph.neighbors(origin))


def test_vertex_navigation_wraps_at_both_boundaries_and_same_vertex_is_zero_cost(app):
    app.go("planner")
    vertices = sorted(app.circuit.graph.vertices)
    first, last = vertices[0], vertices[-1]
    app.target = last

    # Equivalence boundary: advancing from the maximum ID wraps to the minimum.
    app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT, mod=0))
    assert app.target == first

    # The Shift-modified path changes the source, including minimum-ID wraparound.
    app.source = first
    app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT, mod=pygame.KMOD_SHIFT))
    assert app.source == last

    # BVA at equal endpoints: one vertex, no road, and exactly zero cost.
    app.target = last
    route = app.planned_route(PROFILES["Balanced"])
    assert route.vertices == [last]
    assert route.edges == []
    assert route.cost == 0


def test_ordered_lap_and_algorithm_toggle_are_reachable_from_planner_controls(app):
    app.go("planner")
    app.time = app.planner_entered + 1.0
    app.buttons = []
    app.draw_planner()

    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(915, 181)))
    assert app.ordered_plan
    route = app.planned_route(PROFILES["Balanced"])
    assert route.vertices[0] == app.source
    assert route.vertices[-1] == app.circuit.start
    checkpoint_positions = [route.vertices.index(checkpoint)
                            for checkpoint in app.ordered_destinations()[:-1]]
    assert checkpoint_positions == sorted(checkpoint_positions)

    app.buttons = []
    app.draw_planner()
    assert app.route_algorithm == "dijkstra"
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(965, 635)))
    assert app.route_algorithm == "astar"
    assert app.planned_route(PROFILES["Balanced"]).cost == pytest.approx(route.cost)


def test_disconnected_network_renders_unreachable_route_without_crashing(app):
    app.go("planner")
    for road in app.circuit.graph.edges.values():
        road.status = "blocked"
    app._planner_key = None

    route = app.planned_route(PROFILES["Balanced"])
    assert route.vertices == []
    assert route.edges == []
    assert route.cost == float("inf")

    app.buttons = []
    app.draw_planner()
    assert app.buttons
    assert app.screen == "planner"


def test_planner_action_hitboxes_stay_inside_expanded_panel(app):
    app.go("planner")
    app.time = app.planner_entered + 1.0
    app.buttons = []
    app.draw_planner()

    panel = pygame.Rect(860, 202, 380, 578)
    planner_actions = [rect for rect, _action in app.buttons
                       if rect.left >= 885 and rect.top >= 531]
    assert len(planner_actions) == 7
    assert all(panel.contains(rect) for rect in planner_actions)
    assert planner_actions[-1].bottom == 716
