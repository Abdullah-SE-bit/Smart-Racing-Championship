"""Verify backwards playback and invalidation with mutable race-planning data."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from smart_racing.ui.app import App


def test_heap_recording_rewinds_the_actual_tree_and_invalidates_when_priority_changes():
    app = App()
    try:
        app.go("lab")
        app.reduced_motion = True
        app.lab_algorithm = "Event heap"
        trace, _ = app.lab_result()
        before_pop = next(i for i, step in enumerate(trace) if step["action"] == "heap extract")
        keys = tuple(trace[before_pop - 1]["keys"])
        assert sorted(trace[before_pop]["keys"]) == sorted(keys)[1:]
        assert keys[0] == min(keys)

        def frame(step):
            app.lab_step = step
            app.buttons.clear()
            app.draw_lab()
            return pygame.image.tostring(app.surface.subsurface((60, 242, 760, 375)), "RGB")

        tree, extracted = frame(before_pop), frame(before_pop + 1)
        assert tree != extracted
        app.step_lab(-1)
        assert frame(app.lab_step) == tree

        road = min(app.circuit.graph.edges.values(), key=lambda edge: edge.id)
        road.base_time = .01
        updated, _ = app.lab_result()
        assert updated[before_pop - 1]["keys"][0][0] == .01
        assert tuple(trace[before_pop - 1]["keys"]) == keys
    finally:
        pygame.quit()
