"""Create the project's original, dependency-free synthesized WAV sound pack."""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path


RATE = 22_050
OUT = Path(__file__).resolve().parents[1] / "assets" / "audio"


def write(name: str, samples: list[float], *, loop: bool = False) -> None:
    # Short equal-power loop seam avoids a click at the ambience wrap point.
    if loop:
        seam = min(round(RATE * 0.035), len(samples) // 2)
        for i in range(seam):
            t = i / max(1, seam - 1)
            left, right = samples[i], samples[-seam + i]
            samples[i] = right * (1 - t) + left * t
            samples[-seam + i] = right * (1 - t) + left * t
    peak = max((abs(s) for s in samples), default=1.0) or 1.0
    gain = min(0.88 / peak, 1.0)
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / name), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x * gain)) * 32767)) for x in samples))


def tone(duration: float, frequency: float, *, end_frequency: float | None = None,
         wave_kind: str = "sine", attack: float = .015, release: float = .15,
         amplitude: float = .5, harmonics: tuple[tuple[float, float], ...] = ()) -> list[float]:
    count = round(duration * RATE)
    end_frequency = end_frequency or frequency
    values = []
    for index in range(count):
        t = index / RATE
        phase = 2 * math.pi * (frequency * t + (end_frequency - frequency) * t * t / (2 * duration))
        if wave_kind == "triangle":
            fundamental = 2 / math.pi * math.asin(math.sin(phase))
        elif wave_kind == "saw":
            fundamental = 2 / math.pi * math.atan(math.tan(phase / 2))
        else:
            fundamental = math.sin(phase)
        env = min(1.0, t / max(attack, .001)) * min(1.0, (duration - t) / max(release, .001))
        sample = fundamental + sum(weight * math.sin(phase * harmonic) for harmonic, weight in harmonics)
        values.append(amplitude * env * sample)
    return values


def cue(parts: list[tuple[float, list[float]]], duration: float) -> list[float]:
    result = [0.0] * round(duration * RATE)
    for start, values in parts:
        offset = round(start * RATE)
        for index, value in enumerate(values):
            if offset + index < len(result):
                result[offset + index] += value
    return result


def ambience(name: str, seconds: float, notes: tuple[tuple[float, float, float], ...], *, engine=False) -> None:
    count = round(seconds * RATE)
    result = [0.0] * count
    randomizer = random.Random(187 if engine else 53)
    for frequency, start, length in notes:
        wave_data = tone(length, frequency, end_frequency=frequency * (1.015 if engine else .995),
                         wave_kind="saw" if engine else "sine", attack=.3, release=.35,
                         amplitude=.11 if engine else .16,
                         harmonics=((2, .38), (3, .2), (4, .1)) if engine else ((2, .18),))
        offset = round(start * RATE)
        for i, value in enumerate(wave_data):
            if offset + i < count:
                swell = .78 + .22 * math.sin(2 * math.pi * i / max(1, len(wave_data)))
                result[offset + i] += value * swell
    # A subtle air bed: filtered-ish noise, deliberately far below the tonal layers.
    if engine:
        for i in range(count):
            result[i] += randomizer.uniform(-.018, .018)
    write(name, result, loop=True)


def main() -> None:
    cue_defs = {
        "focus": cue([(0, tone(.075, 680, end_frequency=880, attack=.008, release=.055, amplitude=.22))], .09),
        "confirm": cue([(0, tone(.12, 520, end_frequency=760, attack=.008, release=.08, amplitude=.35)),
                        (.045, tone(.16, 780, end_frequency=1040, attack=.008, release=.11, amplitude=.25))], .23),
        "transition": cue([(0, tone(.24, 210, end_frequency=620, wave_kind="triangle", attack=.025, release=.15, amplitude=.25)),
                           (.05, tone(.22, 420, end_frequency=840, attack=.02, release=.15, amplitude=.18))], .29),
        "countdown": cue([(0, tone(.38, 880, end_frequency=1040, attack=.008, release=.12, amplitude=.3))], .4),
        "launch": cue([(0, tone(.72, 110, end_frequency=660, wave_kind="saw", attack=.02, release=.35, amplitude=.35,
                                harmonics=((2, .35), (3, .17), (4, .08))))], .75),
        "nitro": cue([(0, tone(.43, 130, end_frequency=1250, wave_kind="saw", attack=.005, release=.28, amplitude=.38,
                               harmonics=((2, .3), (3, .16)))),
                       (.08, tone(.3, 1450, end_frequency=820, attack=.003, release=.24, amplitude=.16))], .51),
        "checkpoint": cue([(0, tone(.2, 740, end_frequency=990, attack=.008, release=.13, amplitude=.3)),
                            (.09, tone(.25, 990, end_frequency=1320, attack=.01, release=.16, amplitude=.26))], .38),
        "warning": cue([(0, tone(.24, 300, end_frequency=220, wave_kind="triangle", attack=.012, release=.1, amplitude=.36)),
                         (.27, tone(.24, 300, end_frequency=220, wave_kind="triangle", attack=.012, release=.1, amplitude=.36))], .55),
        "finish": cue([(0, tone(.24, 660, attack=.01, release=.16, amplitude=.27)),
                        (.17, tone(.25, 880, attack=.01, release=.17, amplitude=.28)),
                        (.36, tone(.56, 1108, attack=.02, release=.42, amplitude=.3))], .96),
    }
    for name, samples in cue_defs.items():
        write(f"{name}.wav", samples)
    # Restrained cinematic pulse for the garage; engine texture for track action.
    ambience("menu-ambience.wav", 8.0, ((55, 0, 3.8), (82.4, 0, 3.8), (110, 0, 3.8),
                                         (65.4, 4, 3.8), (98, 4, 3.8), (130.8, 4, 3.8)))
    ambience("race-ambience.wav", 6.0, ((42, 0, 5.8), (63, 0, 5.8), (84, 0, 5.8)), engine=True)
    ambience("race-rev.wav", 6.0, ((70, 0, 5.8), (105, 0, 5.8), (140, 0, 5.8)), engine=True)
    ambience("race-boost.wav", 6.0, ((105, 0, 5.8), (157, 0, 5.8), (210, 0, 5.8), (420, 0, 5.8)), engine=True)


if __name__ == "__main__":
    main()
