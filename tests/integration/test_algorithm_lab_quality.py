"""Risk-based boundary and state-transition checks for the Algorithm Lab."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from smart_racing.ui.app import App, LAB_ALGORITHMS
from smart_racing.tracks.generator import generate_circuit


@pytest.mark.parametrize("initial,amount,expected", [
    (0, -1, 0),
    (0, 0, 0),
    (0, 1, 1),
    (3, -1, 2),
    (3, 1, 4),
    (29, 1, 29),
    (29, 100, 29),
    (-100, 1, 0),
    (100, -1, 29),
    (100, -100, 0),
])
def test_step_boundaries_clamp_to_current_trace(initial, amount, expected):
    app = App()
    try:
        app.lab_algorithm = "BFS"
        app.lab_step = initial
        app.step_lab(amount)
        assert app.lab_step == expected
        assert not app.lab_playing
    finally:
        pygame.quit()


@pytest.mark.parametrize("generated", [False, True])
@pytest.mark.parametrize("algorithm", LAB_ALGORITHMS)
def test_each_lab_trace_boundary_renders_on_authored_and_generated_tracks(generated, algorithm):
    app = App()
    try:
        if generated:
            app.circuit = generate_circuit(42)
            app.source = app.circuit.start
            app.target = app.circuit.checkpoints[3]
        app.lab_algorithm = algorithm
        trace, description = app.lab_result()
        assert description
        if not trace:
            assert algorithm in {"Knapsack", "Greedy"}
        for count in sorted({0, 1, max(0, len(trace) // 2), len(trace), len(trace) + 1}):
            app.lab_step = count
            app.buttons.clear()
            app.draw_lab()
            assert app.buttons
            assert app.lab_step == count
    finally:
        pygame.quit()


@pytest.mark.parametrize("algorithm", LAB_ALGORITHMS)
def test_algorithm_trace_is_stable_across_redraw_and_does_not_mutate_race(algorithm):
    app = App()
    try:
        app.start_race()
        app.race.tick(.2)
        app.lab_algorithm = algorithm
        trace, _ = app.lab_result()
        before = repr(trace)
        state = [(r.vertex, r.edge_id, r.edge_progress, r.fuel, r.nitro) for r in app.race.racers]
        for count in {0, len(trace) // 2, len(trace)}:
            app.lab_step = count
            app.buttons.clear()
            app.draw_lab()
        assert repr(app.lab_result()[0]) == before
        assert [(r.vertex, r.edge_id, r.edge_progress, r.fuel, r.nitro) for r in app.race.racers] == state
    finally:
        pygame.quit()


def test_algorithm_switch_and_live_standings_invalidate_trace_and_reset_step():
    app = App()
    try:
        app.lab_algorithm = "BFS"
        first, _ = app.lab_result()
        app.lab_step = len(first)
        app.change_lab(1)
        assert app.lab_algorithm == "DFS"
        assert app.lab_step == 0
        dfs_trace, _ = app.lab_result()
        assert dfs_trace is not first

        app.prepare_championship()
        app.lab_algorithm = "Top-k"
        first, _ = app.lab_result()
        app.entries[1].total_points += 100
        changed, _ = app.lab_result()
        assert changed is not first
        assert changed != first
    finally:
        pygame.quit()


def test_playback_caps_at_end_then_replays_and_pause_freezes_trace():
    app = App()
    try:
        app.lab_algorithm = "BFS"
        trace, _ = app.lab_result()
        app.go("lab")
        app.reduced_motion = True
        app.lab_step = len(trace) - .1
        app.lab_playing = True
        class FastClock:
            def tick(self, fps):
                return 100

        app.clock = FastClock()
        calls = 0

        def event_queue():
            nonlocal calls
            calls += 1
            return [pygame.event.Event(pygame.QUIT)] if calls == 3 else []

        original_get = pygame.event.get
        pygame.event.get = event_queue
        app.present = lambda: None
        try:
            app.run()
        finally:
            pygame.event.get = original_get
        assert app.lab_step == len(trace)
        assert not app.lab_playing

        app.toggle_lab()
        assert app.lab_playing and app.lab_step == 0
    finally:
        pygame.quit()


@pytest.mark.parametrize("algorithm", ["BFS", "Event heap", "Merge sort", "Knapsack"])
def test_algorithm_motion_animates_between_manual_steps_and_respects_reduced_motion(algorithm):
    app = App()
    try:
        app.go("lab")
        app.lab_algorithm = algorithm
        app.lab_playing = False
        app.reduced_motion = False
        trace, _ = app.lab_result()
        assert trace

        def board_at(elapsed):
            app.time = elapsed
            app.buttons.clear()
            app.draw_lab()
            return pygame.image.tostring(app.surface.subsurface((60, 242, 760, 375)), "RGB")

        app.step_lab(1)
        first = board_at(app.lab_step_started + .02)
        settled = board_at(app.lab_step_started + .3)
        assert first != settled

        app.reduced_motion = True
        still = board_at(app.lab_step_started + .02)
        later = board_at(app.lab_step_started + 5)
        assert still == later
    finally:
        pygame.quit()

