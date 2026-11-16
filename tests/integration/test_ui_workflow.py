import os
import subprocess
import sys
from dataclasses import replace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from smart_racing.tracks.circuits import load_circuit, save_circuit
from smart_racing.tracks import generator
from smart_racing.tracks.generator import generate_circuit
from smart_racing.algorithms.routing.shortest import shortest_path
from smart_racing.championship.standings import leaders, standings
from smart_racing.core.graph import Edge, Graph, Vertex
from smart_racing.ui.app import ACCENT, MUTED, PANEL, TEXT, App, LAB_ALGORITHMS, PROFILES


def test_all_screens_render_and_primary_navigation():
    app = App()
    try:
        for name, draw in (("menu", app.draw_menu), ("settings", app.draw_settings),
                           ("planner", app.draw_planner), ("compare", app.draw_comparison), ("lab", app.draw_lab)):
            app.go(name)
            app.buttons = []
            app.background()
            draw()
            assert app.buttons
        for algorithm in LAB_ALGORITHMS:
            app.lab_algorithm = algorithm
            trace, description = app.lab_result()
            assert trace and description
        app.change_lab_speed()
        assert app.lab_speed == 6
        app.step_lab(1)
        assert not app.lab_playing and app.lab_step == 1
        paths = {tuple(shortest_path(app.circuit.graph, 0, 4, profile).vertices) for profile in PROFILES.values()}
        assert len(paths) > 1
        app.ordered_plan = True
        ordered = app.planned_route(PROFILES["Balanced"])
        assert ordered.vertices[0] == ordered.vertices[-1] == 0
        assert [v for v in ordered.vertices if v in app.circuit.checkpoints] == app.circuit.checkpoints
        app.demonstrate_rejection()
        assert app.validation_message.startswith("Rejected:")
        app.start_race(championship=True)
        app.background()
        app.draw_race()
        app.race.elapsed = app.race.time_limit
        app.finish_race()
        app.background()
        app.draw_dashboard()
        app.go("standings")
        app.background()
        app.draw_standings()
        assert app.screen == "standings"
        assert app.recorded
        app.next_championship_race()
        assert app.screen == "planner" and app.track_index == 1
        app.start_planned_race()
        assert app.screen == "race" and app.track_index == 1
    finally:
        pygame.quit()


def test_seeded_generated_circuits_are_repeatable(tmp_path):
    first, second = generate_circuit(42), generate_circuit(42)
    trace = []
    observed = generate_circuit(42, trace=trace)
    assert first.graph.vertices == second.graph.vertices
    assert first.graph.edges == second.graph.edges
    assert observed.graph.vertices == first.graph.vertices
    assert observed.graph.edges == first.graph.edges
    assert trace[-1]["stage"] == "accepted"
    assert len(first.checkpoints) == 10
    assert sum(edge.shortcut for edge in first.graph.edges.values()) >= 2
    path = tmp_path / "generated.json"
    save_circuit(first, path)
    assert load_circuit(path).graph.edges == first.graph.edges


def test_saved_circuit_with_nonconsecutive_ids_can_be_selected_and_raced(tmp_path):
    circuit = generate_circuit(42)
    graph = Graph()
    for vertex in circuit.graph.vertices.values():
        graph.add_vertex(replace(vertex, id=vertex.id + 100))
    for edge in circuit.graph.edges.values():
        graph.add_edge(replace(edge, id=edge.id + 500,
                               source=edge.source + 100, target=edge.target + 100))
    circuit.graph = graph
    circuit.start += 100
    circuit.checkpoints = [vertex + 100 for vertex in circuit.checkpoints]
    circuit.main_route = [vertex + 100 for vertex in circuit.main_route]
    path = tmp_path / "renumbered.json"
    save_circuit(circuit, path)

    app = App()
    try:
        app.circuit_paths.append(path)
        app.track_index = len(app.circuit_paths) - 2
        app.set_track(1)
        assert app.source == circuit.start
        assert app.target in circuit.checkpoints
        app.draw_planner()
        app.start_race()
        assert app.race.racers[0].vertex == circuit.start
        for _ in range(30):
            app.race.tick(1)
        assert any("oil" in message for message in app.race.event_log)
        assert any("block" in message for message in app.race.event_log)
    finally:
        pygame.quit()


def test_generation_retries_are_bounded_and_deterministic(monkeypatch):
    original = generator._generate_candidate
    attempts = []

    def fail_once(seed, attempt):
        attempts.append(attempt)
        if attempt == 0:
            raise ValueError("invalid candidate")
        return original(seed, attempt)

    monkeypatch.setattr(generator, "_generate_candidate", fail_once)
    assert generator.generate_circuit(42, max_attempts=2).name == "Generated 42"
    assert attempts == [0, 1]
    attempts.clear()
    with pytest.raises(ValueError, match="after 1 attempts"):
        generator.generate_circuit(42, max_attempts=1)


def test_generation_trace_records_actual_rejection_and_retry(monkeypatch):
    original = generator._generate_candidate

    def fail_once(seed, attempt, trace=None):
        if attempt == 0:
            raise ValueError("candidate violates spacing")
        return original(seed, attempt, trace)

    monkeypatch.setattr(generator, "_generate_candidate", fail_once)
    trace = []
    circuit = generator.generate_circuit(42, max_attempts=2, trace=trace)
    assert circuit.name == "Generated 42"
    assert any(step == {"stage": "rejected", "detail": "candidate violates spacing"} for step in trace)
    assert [step["stage"] for step in trace].count("attempt") == 2
    assert {"checkpoints", "services", "backbone", "roads", "obstacles", "accepted"}.issubset(
        {step["stage"] for step in trace})


def test_generated_circuit_workshop_shows_stages_and_validation():
    app = App()
    try:
        app.generate()
        assert app.screen == "generation"
        assert app.generation_trace[-1]["stage"] == "accepted"
        app.reduced_motion = True
        app.background()
        app.draw_generation()
        app.demonstrate_rejection()
        assert app.validation_message.startswith("Rejected:")
        app.draw_generation()
        app.go("planner")
        app.start_planned_race()
        assert app.race.circuit.name == app.circuit.name
    finally:
        pygame.quit()


def test_complete_three_race_championship():
    app = App()
    try:
        app.start_race(championship=True)
        for race_number in range(3):
            race = app.race
            for _ in range(4000):
                human = race.racers[0]
                if human.edge_id is None and not human.finished and not human.dnf:
                    route = shortest_path(race.circuit.graph, human.vertex, race._destination(human))
                    if len(route.vertices) > 1:
                        race.choose(0, route.vertices[1])
                race.tick(.1)
                if race.over:
                    break
            assert race.over and all(racer.finished for racer in race.racers)
            app.finish_race()
            assert sum(entry.total_points for entry in app.entries) == (race_number + 1) * 70
            app.next_championship_race()
            if race_number < 2:
                assert app.screen == "planner"
                app.start_planned_race()
        assert app.screen == "menu"
    finally:
        pygame.quit()


def test_mouse_and_keyboard_start_and_drive_a_quick_race():
    app = App()
    try:
        app.buttons = []
        app.background()
        app.draw_menu()
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 480)))
        assert app.screen == "race"
        human = app.race.racers[0]
        initial_vertex = human.vertex
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n))
        assert human.nitro == 0
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        for _ in range(100):
            app.race.tick(.1)
            if human.vertex != initial_vertex:
                break
        assert human.vertex != initial_vertex
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        assert app.paused
    finally:
        pygame.quit()


def test_championship_menu_plans_first_circuit_and_preserves_season_order():
    app = App()
    try:
        app.draw_menu()
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 400)))
        assert app.screen == "planner" and app.pending_championship
        first = app.circuit.name
        app.generate()
        assert app.circuit.name == first
        assert "fixed season order" in app.validation_message
        app.start_planned_race()
        assert app.championship and not app.pending_championship
        assert app.race.circuit.name == first
        assert len(app.entries) == 4
    finally:
        pygame.quit()


def test_planner_alternatives_show_real_bounded_paths():
    app = App()
    try:
        app.source, app.target = 0, 4
        app.open_alternatives()
        assert app.screen == "alternatives"
        assert app.alternative_paths
        chosen = shortest_path(app.circuit.graph, 0, 4, PROFILES["Balanced"])
        for path in app.alternative_paths:
            assert path[0] == 0 and path[-1] == 4
            assert path != chosen.vertices and len(path) == len(set(path))
            assert all(any(neighbor == target for neighbor, _ in app.circuit.graph.neighbors(source))
                       for source, target in zip(path, path[1:]))
        app.background()
        app.draw_alternatives()
        app.change_alternative(1)
        assert 0 <= app.alternative_index < len(app.alternative_paths)
        app.target = app.source
        app.open_alternatives()
        assert app.alternative_paths == []
        app.draw_alternatives()
    finally:
        pygame.quit()


def test_route_comparison_animation_uses_actual_vertices_and_respects_reduced_motion():
    app = App()
    try:
        vertices = [0, 2, 7, 9]
        app.time = 0
        assert app.comparison_path(vertices, 0) == "0 ..."
        app.time = 1
        assert app.comparison_path(vertices, 0) == "0 → 2 → 7 → 9"
        app.reduced_motion = True
        app.time = 0
        assert app.comparison_path(vertices, 0) == "0 → 2 → 7 → 9"
        assert app.comparison_path([], 0) == "No route"
    finally:
        pygame.quit()


def test_route_presets_recompute_exact_costs_after_a_road_closes():
    app = App()
    try:
        graph = app.circuit.graph
        app.source, app.target = app.circuit.start, app.circuit.checkpoints[3]
        original = {name: app.planned_route(profile) for name, profile in PROFILES.items()}
        assert len({tuple(route.vertices) for route in original.values()}) > 1
        blocked_edge = original["Balanced"].edges[-1]
        graph.edges[blocked_edge].status = "blocked"
        for name, profile in PROFILES.items():
            route = app.planned_route(profile)
            assert route.vertices and blocked_edge not in route.edges
            assert route.cost == pytest.approx(sum(profile.cost(graph.edges[edge]) for edge in route.edges))
            assert route.cost == pytest.approx(shortest_path(graph, app.source, app.target, profile, "astar").cost)
        app.ordered_plan = True
        for profile in PROFILES.values():
            route = app.planned_route(profile)
            assert route.vertices and blocked_edge not in route.edges
            assert [vertex for vertex in route.vertices if vertex in app.circuit.checkpoints] == app.circuit.checkpoints
        app.draw_comparison()
    finally:
        pygame.quit()


def test_live_championship_leaders_follow_changed_results_and_every_k():
    app = App()
    try:
        app.prepare_championship()
        app.top_k_count = 1
        labels = []
        app.label = lambda text, *args, **kwargs: labels.append(str(text))
        app.entries[1].total_points = 25
        app.draw_standings()
        assert "#1  NOVA" in labels
        labels.clear()
        app.entries[2].total_points = 30
        app.draw_standings()
        assert "#1  BLAZE" in labels
        for k in range(1, len(app.entries) + 1):
            app.top_k_count = k
            assert leaders(app.entries, k) == standings(app.entries)[:k]
        app.top_k_count = len(app.entries)
        app.change_top_k()
        assert app.top_k_count == 1
    finally:
        pygame.quit()


def test_race_hud_uses_actual_checkpoint_count_and_shows_feedback():
    app = App()
    try:
        app.start_race()
        race = app.race
        graph = race.circuit.graph
        graph.add_vertex(Vertex(100, 500, 350, "checkpoint", 11))
        graph.add_edge(Edge(1000, race.circuit.checkpoints[-1], 100, 1, 1, 1))
        graph.add_edge(Edge(1001, 100, race.circuit.start, 1, 1, 1))
        race.circuit.checkpoints.append(100)
        race.racers[0].next_checkpoint = 10
        race.service_active[next(v.id for v in graph.vertices.values() if v.kind == "nitro")] = False
        race.event_log.append("YOU: collected nitro")
        labels = []
        app.label = lambda text, *args, **kwargs: labels.append(str(text))
        app.draw_race()
        assert "NEXT CHECKPOINT   11" in labels
        assert "YOU: collected nitro" in labels
    finally:
        pygame.quit()


def test_module_entry_point_runs_headless_smoke_check():
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    result = subprocess.run([sys.executable, "-m", "smart_racing", "--smoke-test"],
                            env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


def test_reduced_motion_and_text_contrast():
    def luminance(color):
        channels = [value / 255 for value in color]
        channels = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4 for value in channels]
        return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2]

    for color in (TEXT, MUTED, ACCENT):
        ratio = (luminance(color) + .05) / (luminance(PANEL) + .05)
        assert ratio >= 4.5
    app = App()
    try:
        app.go("settings")
        assert app.transition_remaining > 0
        app.toggle_motion()
        app.go("menu")
        assert app.reduced_motion and app.transition_remaining == 0
    finally:
        pygame.quit()
