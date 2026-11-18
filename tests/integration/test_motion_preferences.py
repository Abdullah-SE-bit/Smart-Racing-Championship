"""A saved accessibility choice must apply before the first interactive frame."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from smart_racing.ui.app import App


def test_relaunch_after_changing_motion(tmp_path):
    preferences = tmp_path / "profile" / "preferences.json"
    try:
        first = App(settings_file=preferences)
        first.toggle_motion()
        second = App(settings_file=preferences)
        second.start_intro()
        assert second.reduced_motion and not second.intro_active
        second.go("settings")
        assert second.transition_remaining == 0
        second.toggle_motion()
        third = App(settings_file=preferences)
        third.start_intro()
        assert third.intro_active
    finally:
        pygame.quit()


def test_corrupt_preference_allows_start_and_unwritable_preference_allows_toggle(tmp_path):
    preferences = tmp_path / "preferences.json"
    preferences.write_text("{", encoding="utf-8")
    try:
        app = App(settings_file=preferences)
        app.start_intro()
        assert app.intro_active
        app.settings_file = preferences / "inside-a-file.json"
        app.toggle_motion()
        assert app.reduced_motion
    finally:
        pygame.quit()
