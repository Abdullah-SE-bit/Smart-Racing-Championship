"""Original generated game sounds and a small, presentation-only soundscape."""

from pathlib import Path

import pygame


class Soundscape:
    """Mix menu ambience, race engine, and short cues without touching game state."""

    LEVELS = (0.0, 0.28, 0.62, 1.0)
    CUES = (
        "focus", "confirm", "transition", "countdown", "launch", "nitro",
        "checkpoint", "warning", "finish",
    )

    def __init__(self, asset_dir: Path, level: int = 2):
        self.level = max(0, min(int(level), len(self.LEVELS) - 1))
        self.available = False
        self._cue_sounds = {}
        self._loops = {}
        self._loop_channels = {}
        self._loop_targets = {}
        self._channels = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            pygame.mixer.set_num_channels(max(8, pygame.mixer.get_num_channels()))
            self._channels = {
                "cues": pygame.mixer.Channel(0),
                "menu": pygame.mixer.Channel(1),
                "race": pygame.mixer.Channel(2),
                "rev": pygame.mixer.Channel(3),
                "boost": pygame.mixer.Channel(4),
            }
            for key in ("menu", "race", "rev", "boost"):
                self._channels[key].set_volume(0)
            for name in self.CUES:
                path = asset_dir / f"{name}.wav"
                if path.exists():
                    self._cue_sounds[name] = pygame.mixer.Sound(str(path))
            loop_assets = {"menu": "menu-ambience.wav", "race": "race-ambience.wav",
                           "rev": "race-rev.wav", "boost": "race-boost.wav"}
            for name, filename in loop_assets.items():
                path = asset_dir / filename
                if path.exists():
                    self._loops[name] = pygame.mixer.Sound(str(path))
                    self._loop_channels[name] = self._channels[name]
            self._loop_targets = {name: 0.0 for name in self._loops}
            self.available = bool(self._cue_sounds or self._loops)
        except (pygame.error, OSError):
            # Audio hardware is optional; the game remains fully playable headless.
            self.available = False

    @property
    def volume(self) -> float:
        return self.LEVELS[self.level]

    def set_level(self, level: int) -> None:
        self.level = max(0, min(int(level), len(self.LEVELS) - 1))
        self._apply_volumes()

    def cue(self, name: str) -> None:
        if not self.available or self.volume <= 0 or name not in self._cue_sounds:
            return
        channel = self._channels["cues"]
        channel.set_volume(self.volume)
        channel.play(self._cue_sounds[name])

    def scene(self, name: str) -> None:
        """Crossfade ambience; race-rev and race-boost add speed-sensitive engine layers."""
        if not self.available:
            return
        selected = {"race-rev": "rev", "race-boost": "boost"}.get(name, name)
        self._loop_targets = {key: (1.0 if key == selected else 0.0) for key in self._loops}
        for key, sound in self._loops.items():
            channel = self._loop_channels[key]
            if key == selected and not channel.get_busy():
                channel.set_volume(0)
                channel.play(sound, loops=-1)
            if key != selected and channel.get_busy():
                self._loop_targets[key] = 0.0

    def update(self, delta: float) -> None:
        """Smoothly mix ambience levels, independently of simulation time."""
        if not self.available:
            return
        step = min(1.0, max(0.0, delta) * 2.8)
        for name, target in self._loop_targets.items():
            channel = self._loop_channels[name]
            current = channel.get_volume()
            mix = 0.19 if name in ("rev", "boost") else 0.26
            desired = target * self.volume * mix
            value = current + (desired - current) * step
            channel.set_volume(value)
            if target == 0 and value < 0.006 and channel.get_busy():
                channel.stop()

    def _apply_volumes(self) -> None:
        for name, target in self._loop_targets.items():
            mix = 0.19 if name in ("rev", "boost") else 0.26
            self._loop_channels[name].set_volume(target * self.volume * mix)

    def close(self) -> None:
        if self.available:
            for channel in self._channels.values():
                channel.stop()
