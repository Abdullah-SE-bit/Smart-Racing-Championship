import os
import hashlib
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
from smart_racing.algorithms.routing.shortest import Route, shortest_path
from smart_racing.championship.standings import leaders, standings
from smart_racing.core.graph import Edge, Graph, Vertex
from smart_racing.ui.app import ACCENT, BACKGROUND, EMPHASIS, GAUGE_TRACK, INTRO_DURATION, MUTED, PANEL, PLANNER_MAP, PRIMARY, TEXT, App, LAB_ALGORITHMS, PROFILES


def test_startup_intro_finishes_and_skip_does_not_activate_menu():
    app = App()
    try:
        app.start_intro()
        assert app.intro_active and app.screen == "menu" and app.race is None
        app.advance_intro(INTRO_DURATION - .1)
        assert app.intro_active and app.race is None
        app.advance_intro(.1)
        assert not app.intro_active and app.screen == "menu"

        for event in (pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
                      pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE),
                      pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
                      pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 425))):
            app.start_intro()
            app.event(event)
            assert not app.intro_active and app.screen == "menu" and app.race is None
        app.start_intro()
        app.event(pygame.event.Event(pygame.VIDEORESIZE, size=(960, 600)))
        assert app.intro_active and app.window.get_size() == (960, 600)
        app.event(pygame.event.Event(pygame.QUIT))
        assert not app.running
    finally:
        pygame.quit()


def test_reduced_motion_skips_startup_intro():
    app = App()
    try:
        app.reduced_motion = True
        app.start_intro()
        assert not app.intro_active and app.screen == "menu"
    finally:
        pygame.quit()


def test_startup_intro_animates_distinct_frames_without_advancing_race():
    app = App()
    try:
        app.start_intro()
        frames = []
        for moment in (.7, 1.6, 2.5, 3.5):
            app.intro_elapsed = moment
            app.draw_intro()
            frames.append(hashlib.sha256(pygame.image.tostring(app.surface, "RGB")).digest())
        assert len(set(frames)) == 4
        assert app.race is None and app.screen == "menu"
        assert app.intro_elapsed == 3.5
    finally:
        pygame.quit()


def test_blue_menu_background_is_consistent_and_venue_screens_follow_track():
    app = App()
    try:
        app.reduced_motion = True
        frames = []
        for path in app.authored_paths:
            app.circuit = load_circuit(path)
            app.draw_pit_background()
            frames.append(hashlib.sha256(pygame.image.tostring(app.surface, "RGB")).digest())
        assert len(frames) == 3 and len(set(frames)) == 1

        app.screen = "planner"
        venue_frames = []
        for path in app.authored_paths:
            app.circuit = load_circuit(path)
            app.surface.fill(BACKGROUND)
            app.draw_pit_background()
            venue_frames.append(hashlib.sha256(pygame.image.tostring(app.surface, "RGB")).digest())
        assert len(set(venue_frames)) == 3
    finally:
        pygame.quit()


def test_menu_selects_blue_hero_art_while_other_screens_select_venue_art(monkeypatch):
    import smart_racing.ui.app as app_module

    app = App()
    requested = []
    monkeypatch.setattr(app_module, "load_circuit_backdrop",
                        lambda name: requested.append(name) or app.pit_backdrop)
    try:
        app.screen = "menu"
        app.draw_pit_background()
        assert requested[-1] == "aurora-circuit-dusk.png"

        app.screen = "planner"
        app.circuit = load_circuit(app.authored_paths[0])
        app.draw_pit_background()
        assert requested[-1] == "neon-harbor-night.png"
    finally:
        pygame.quit()


def test_main_loop_shows_intro_then_menu_without_starting_race(monkeypatch):
    app = App()
    frames = []

    class FastClock:
        def tick(self, fps):
            return 100

    def events():
        if len(frames) >= 45:
            return [pygame.event.Event(pygame.QUIT)]
        return []

    app.clock = FastClock()
    monkeypatch.setattr(pygame.event, "get", events)
    monkeypatch.setattr(app, "draw_intro", lambda: frames.append("intro"))
    monkeypatch.setattr(app, "draw_menu", lambda: frames.append("menu"))
    monkeypatch.setattr(app, "present", lambda: None)
    app.run()
    assert frames[0] == "intro" and frames[-1] == "menu"
    assert app.race is None and app.screen == "menu"


def test_menu_track_selection_navigation_and_reduced_motion():
    app = App()
    try:
        def render_menu(time):
            app.time = time
            app.buttons = []
            app.draw_menu()
            return pygame.image.tostring(app.surface, "RGB")

        app.reduced_motion = True
        still = render_menu(0)
        assert render_menu(10) == still
        app.reduced_motion = False
        assert render_menu(10) != render_menu(0)

        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(438, 679)))
        assert app.track_index == 1
        assert render_menu(0) != still
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(150, 498)))
        assert app.screen == "planner"
        app.go("menu")
        render_menu(0)
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB, mod=0))
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
        assert app.screen == "planner" and app.pending_championship
    finally:
        pygame.quit()


def test_backdrop_and_button_motion_respect_reduced_motion(monkeypatch):
    app = App()
    try:
        assert app.pit_backdrop.get_width() >= 1280
        assert app.pit_backdrop.get_height() >= 800
        monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (-100, -100))

        def backdrop_at(time):
            app.time = time
            app.draw_pit_background()
            return pygame.image.tostring(app.surface, "RGB")

        def button_at(time):
            app.time = time
            app.surface.fill((0, 0, 0))
            app.buttons = []
            app.menu_button((48, 319, 420, 65), "CHAMPIONSHIP", None, lambda: None, True)
            return pygame.image.tostring(app.surface.subsurface((48, 319, 420, 65)), "RGB")

        app.reduced_motion = False
        app.screen = "menu"
        assert backdrop_at(0) == backdrop_at(5)
        app.screen = "settings"
        assert backdrop_at(0) != backdrop_at(5)
        assert button_at(0) != button_at(1)
        app.reduced_motion = True
        app.screen = "menu"
        assert backdrop_at(0) == backdrop_at(5)
        app.screen = "settings"
        assert backdrop_at(0) == backdrop_at(5)
        assert button_at(0) == button_at(1)
    finally:
        pygame.quit()


def test_settings_screen_changes_options_and_returns_to_menu():
    app = App()
    try:
        app.go("settings")
        app.buttons = []
        app.draw_settings()
        for position in ((900, 380), (900, 480), (900, 575)):
            app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position))
        assert app.laps_setting == 3
        assert app.limit_setting == 360
        assert app.reduced_motion
        app.buttons = []
        app.draw_settings()
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB, mod=0))
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
        assert app.screen == "menu"
    finally:
        pygame.quit()


def test_planner_map_selection_and_separate_tools():
    app = App()
    try:
        app.open_quick_planner()
        app.buttons = []
        app.draw_planner()
        selected = app.circuit.checkpoints[1]
        point = app.map_positions(PLANNER_MAP, app.circuit)[selected]
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))
        assert app.target == selected
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(130, 682)))
        assert app.screen == "refuel"
        app.go("planner")
        app.buttons = []
        app.draw_planner()
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(350, 682)))
        assert app.screen == "alternatives"
    finally:
        pygame.quit()


def test_planner_route_and_intelligence_panel_animate_without_reduced_motion():
    app = App()
    try:
        app.go("planner")
        frames = []
        for moment in (0.0, .45, 1.0):
            app.time = moment
            app.buttons = []
            app.background()
            app.draw_planner()
            frames.append(hashlib.sha256(pygame.image.tostring(app.surface, "RGB")).digest())
        assert len(set(frames)) == len(frames)
    finally:
        pygame.quit()


def test_reduced_motion_keeps_planner_route_and_panel_static():
    app = App()
    try:
        app.reduced_motion = True
        app.go("planner")
        frames = []
        for moment in (.1, .8):
            app.time = moment
            app.buttons = []
            app.background()
            app.draw_planner()
            frames.append(hashlib.sha256(pygame.image.tostring(app.surface, "RGB")).digest())
        assert frames[0] == frames[1]
    finally:
        pygame.quit()


def test_race_presentation_does_not_advance_simulation():
    app = App()
    try:
        app.start_race()
        app.race.tick(.3)
        before = [(racer.vertex, racer.edge_id, racer.edge_progress, racer.fuel)
                  for racer in app.race.racers]
        elapsed = app.race.elapsed
        app.buttons = []
        app.draw_race()
        app.draw_race()
        assert app.race.elapsed == elapsed
        assert [(racer.vertex, racer.edge_id, racer.edge_progress, racer.fuel)
                for racer in app.race.racers] == before
    finally:
        pygame.quit()


def test_race_hud_resource_and_checkpoint_indicators_follow_state():
    app = App()
    try:
        app.start_race()
        human = app.race.racers[0]
        human.nitro = 1
        human.next_checkpoint = 2
        app.buttons = []
        app.draw_race()
        assert app.surface.get_at((1155, 364))[:3] == EMPHASIS
        assert app.surface.get_at((1176, 364))[:3] == GAUGE_TRACK
        assert app.surface.get_at((890, 419))[:3] == ACCENT
        assert app.surface.get_at((958, 419))[:3] == GAUGE_TRACK
        human.nitro = 3
        human.next_checkpoint = len(app.circuit.checkpoints)
        app.buttons = []
        app.draw_race()
        assert app.surface.get_at((1197, 364))[:3] == EMPHASIS
        assert app.surface.get_at((958, 419))[:3] == ACCENT
    finally:
        pygame.quit()


def test_lab_playback_controls_show_real_trace_progress():
    app = App()
    try:
        app.go("lab")
        app.lab_playing = False
        app.lab_step = 0
        app.buttons = []
        app.draw_lab()
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1100, 490)))
        assert app.lab_step == 1 and not app.lab_playing
        trace, _ = app.lab_result()
        assert trace
        labels = []
        app.label = lambda text, *args, **kwargs: labels.append(str(text))
        app.buttons = []
        app.draw_lab()
        assert f"STEP  1 / {len(trace)}" in labels
        assert str(trace[0].get("action", "step")).upper() in labels
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(950, 550)))
        assert app.lab_step == 0
    finally:
        pygame.quit()


def test_standings_controls_preserve_ranking_and_return_to_results():
    app = App()
    try:
        app.prepare_championship()
        app.entries[1].total_points = 25
        app.entries[2].total_points = 18
        app.go("standings")
        app.buttons = []
        app.draw_standings()
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(800, 255)))
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1050, 255)))
        assert app.sort_method == "Quick" and app.top_k_count == 4
        assert [entry.racer_id for entry in leaders(app.entries, 4)] == [
            entry.racer_id for entry in standings(app.entries)]
        app.buttons = []
        app.draw_standings()
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1000, 650)))
        assert app.screen == "dashboard"
    finally:
        pygame.quit()


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
    assert any(step["stage"] == "one_way" for step in trace)
    assert len(first.checkpoints) == 10
    assert sum(edge.shortcut for edge in first.graph.edges.values()) >= 2
    directed = [edge for edge in first.graph.edges.values() if edge.directed]
    assert len(directed) == 2
    for edge in directed:
        assert any(road.id == edge.id and target == edge.target
                   for target, road in first.graph.neighbors(edge.source))
        assert not any(road.id == edge.id for _, road in first.graph.neighbors(edge.target))
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
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 425)))
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
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 350)))
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


def test_race_controls_support_mouse_actions():
    app = App()
    try:
        app.start_race()

        def click_button(title):
            app.buttons = []
            app.draw_race()
            button = next((rect, action) for rect, action in app.buttons
                          if rect.x == {"NEXT ROAD": 215, "DRIVE": 390, "BOOST": 565,
                                        "REFUEL": 740, "PAUSE": 915}[title])
            app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=button[0].center))

        click_button("NEXT ROAD")
        assert app.selected_road == 1
        expected, expected_road = app.race.options(app.race.racers[0])[1]
        click_button("DRIVE")
        assert app.race.racers[0].desired_target == expected
        assert app.race.racers[0].desired_edge_id == expected_road.id
        click_button("BOOST")
        assert app.race.racers[0].nitro == 0
        click_button("PAUSE")
        assert app.paused
        click_button("PAUSE")
        assert not app.paused
        human = app.race.racers[0]
        human.vertex = next(v.id for v in app.race.circuit.graph.vertices.values() if v.kind == "fuel")
        human.fuel = 50
        click_button("REFUEL")
        assert human.fuel == 90
    finally:
        pygame.quit()


def test_race_hud_explains_unavailable_route_and_insufficient_fuel(monkeypatch):
    app = App()
    try:
        app.start_race()
        race = app.race
        human = race.racers[0]
        roads = race.options(human)
        assert len(roads) >= 2
        human.fuel = 1
        roads[0][1].fuel_cost = 20
        roads[1][1].fuel_cost = .1
        assert race.choose(human.id, roads[0][0], roads[0][1].id)
        race.tick(.1)
        assert human.status == "insufficient fuel for selected road"
        labels = []
        monkeypatch.setattr(app, "label", lambda text, *args, **kwargs: labels.append(str(text)))
        app.draw_race()
        assert "INSUFFICIENT FUEL FOR SELECTED ROAD" in labels

        for _, road in race.options(human):
            road.status = "blocked"
        labels.clear()
        app.draw_race()
        assert any(label.startswith("ROUTE UNAVAILABLE:") for label in labels)
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


@pytest.mark.parametrize("generated", [False, True])
def test_every_algorithm_lab_mode_renders_and_steps_on_real_tracks(generated, monkeypatch):
    app = App()
    try:
        if generated:
            app.circuit = generate_circuit(42)
            app.source = app.circuit.start
            app.target = app.circuit.checkpoints[3]
        for algorithm in LAB_ALGORITHMS:
            app.lab_algorithm = algorithm
            trace, description = app.lab_result()
            assert description
            if not trace:
                assert algorithm in {"Knapsack", "Greedy"}
                assert "No feasible pickup" in description
            app.lab_step = 0
            app.lab_playing = True
            app.step_lab(1)
            assert not app.lab_playing and app.lab_step == 1
            app.toggle_lab()
            assert app.lab_playing
            app.lab_step = len(trace) + 5
            labels = []
            with monkeypatch.context() as context:
                context.setattr(app, "label", lambda text, *args, **kwargs: labels.append(str(text)))
                app.buttons = []
                app.draw_lab()
            assert f"STEP  {len(trace)} / {len(trace)}" in labels
            app.lab_step = 50000
            app.reset_lab()
            assert app.lab_step == 0 and not app.lab_playing
        app.step_lab(-1)
        assert app.lab_step == 0
        app.lab_step = len(trace)
        app.step_lab(1)
        assert app.lab_step == len(trace)
        previous_speed = app.lab_speed
        app.change_lab_speed()
        assert app.lab_speed != previous_speed
    finally:
        pygame.quit()


def test_algorithm_lab_uses_current_track_and_championship_data():
    app = App()
    try:
        app.lab_algorithm = "Knapsack"
        trace, description = app.lab_result()
        pickup = next(vertex.id for vertex in app.circuit.graph.vertices.values() if vertex.kind == "nitro")
        assert trace and trace[0]["item"] == pickup
        assert f"Pickup {pickup}" in description

        app.lab_algorithm = "Merge sort"
        _, description = app.lab_result()
        assert description.startswith("Track checkpoints:")
        app.prepare_championship()
        app.entries[2].total_points = 25
        trace, description = app.lab_result()
        assert trace and description.startswith("Standings: BLAZE")

        app.lab_algorithm = "Event heap"
        trace, description = app.lab_result()
        assert trace and "Track road times" in description
        app.lab_algorithm = "Kruskal"
        app.circuit = generate_circuit(42)
        trace, description = app.lab_result()
        assert trace and "excluded 2 one-way" in description
        for edge in app.circuit.graph.edges.values():
            edge.directed = True
        trace, description = app.lab_result()
        assert not trace and "disconnected" in description
    finally:
        pygame.quit()


def test_refuel_screen_shows_actual_stop_and_planned_fuel(monkeypatch):
    app = App()
    try:
        graph = Graph()
        for vertex in (Vertex(0, 0, 0, "start"), Vertex(1, 1, 0, "fuel"),
                       Vertex(2, 2, 0, "finish")):
            graph.add_vertex(vertex)
        graph.add_edge(Edge(0, 0, 1, 1, 1, 70))
        graph.add_edge(Edge(1, 1, 2, 1, 1, 70))
        app.circuit.graph = graph
        monkeypatch.setattr(app, "planned_route", lambda profile: Route(vertices=[0, 1, 2], edges=[0, 1], cost=2))
        labels = []
        maps = []
        draw_map = app.draw_map
        def record_map(rect, circuit, route, visited):
            maps.append((route, visited))
            return draw_map(rect, circuit, route, visited)
        monkeypatch.setattr(app, "draw_map", record_map)
        monkeypatch.setattr(app, "label", lambda text, *args, **kwargs: labels.append(str(text)))
        app.open_refuel_plan()
        app.draw_refuel_plan()
        assert app.screen == "refuel"
        assert "01   1" in labels
        assert "40.0 units" in labels
        assert maps == [([0, 1], [0, 1, 2])]
        assert any("press F" in label for label in labels)
    finally:
        pygame.quit()


def test_keyboard_navigation_and_planner_vertex_selection():
    app = App()
    try:
        app.draw_menu()
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB, mod=0))
        assert app.keyboard_focus and app.focused_button == 0
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
        assert app.screen == "planner" and app.pending_championship
        before = app.target
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT, mod=0))
        assert app.target != before
        before = app.source
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT, mod=pygame.KMOD_SHIFT))
        assert app.source != before
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0))
        assert app.screen == "menu"
    finally:
        pygame.quit()


def test_resized_window_maps_mouse_to_logical_controls():
    app = App()
    try:
        app.window = pygame.display.set_mode((960, 600), pygame.RESIZABLE)
        assert app.logical_position((75, 321)) == pytest.approx((100, 428))
        app.draw_menu()
        app.present()
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(75, 321)))
        assert app.screen == "race" and not app.championship
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

    for color in (TEXT, MUTED, ACCENT, EMPHASIS):
        ratio = (luminance(color) + .05) / (luminance(PANEL) + .05)
        assert ratio >= 4.5
    assert (luminance(TEXT) + .05) / (luminance(PRIMARY) + .05) >= 4.5
    app = App()
    try:
        app.go("settings")
        assert app.transition_remaining > 0
        app.toggle_motion()
        app.go("menu")
        assert app.reduced_motion and app.transition_remaining == 0
    finally:
        pygame.quit()
