import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from smart_racing.ui.app import App, ROOT
from smart_racing.ui.audio import Soundscape


def test_audio_pack_loads_and_scene_crossfade_is_smooth():
    try:
        sound = Soundscape(ROOT / "assets" / "audio")
        assert sound.available
        assert set(sound.CUES) <= set(sound._cue_sounds)
        sound.scene("menu")
        sound.update(.1)
        menu = sound._loop_channels["menu"].get_volume()
        assert 0 < menu < sound.volume * .26
        sound.scene("race")
        sound.update(.1)
        assert sound._loop_channels["race"].get_busy()
        sound.scene("race-rev")
        sound.update(.1)
        assert sound._loop_channels["rev"].get_busy()
        sound.set_level(0)
        assert sound.volume == 0
        sound.close()
    finally:
        pygame.quit()


def test_sound_level_persists_and_race_events_have_distinct_cues(tmp_path):
    preferences = tmp_path / "preferences.json"
    calls = []
    try:
        app = App(settings_file=preferences)
        app.soundscape.set_level(3)
        app.save_preferences()
        reloaded = App(settings_file=preferences)
        assert reloaded.soundscape.level == 3

        reloaded.soundscape.cue = calls.append
        reloaded.play_race_events(("YOU: nitro activated", "NOVA: finished", "2.0s: block on 4",
                                   "YOU: checkpoint 3 reached", "YOU: refuelling"))
        assert calls == ["nitro", "finish", "warning", "checkpoint"]
        reloaded.soundscape.close()
    finally:
        pygame.quit()


def test_sound_preference_bounds_and_invalid_saved_values(tmp_path):
    preferences = tmp_path / "preferences.json"
    preferences.write_text('{"sound_level": true}', encoding="utf-8")
    try:
        app = App(settings_file=preferences)
        assert app.soundscape.level == 2
        for value, expected in ((-1, 0), (0, 0), (3, 3), (4, 3)):
            app.soundscape.set_level(value)
            assert app.soundscape.level == expected
        app.soundscape.close()
    finally:
        pygame.quit()


def test_circuit_venue_backdrops_are_packaged_and_loaded():
    expected = ("neon-harbor.png", "copper-canyon.png", "aurora-night.png")
    try:
        for name in expected:
            image = ROOT / "assets" / "images" / name
            assert image.is_file() and image.stat().st_size > 10_000
            loaded = pygame.image.load(str(image))
            assert loaded.get_size() == (1600, 1000)
    finally:
        pygame.quit()


def test_missing_optional_sound_assets_degrade_safely(tmp_path):
    try:
        sound = Soundscape(tmp_path)
        assert not sound.available
        sound.scene("race")
        sound.update(.1)
        sound.set_level(1)
        sound.cue("confirm")
        sound.close()
    finally:
        pygame.quit()
