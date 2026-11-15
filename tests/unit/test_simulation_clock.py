from math import nan

import pytest

from smart_racing.game.clock import SimulationClock


def test_different_frame_rates_deliver_identical_simulation_steps():
    sequences = []
    for frames in ([1 / 30] * 30, [1 / 60] * 60, [.1] * 10):
        clock = SimulationClock()
        ticks = []
        for elapsed in frames:
            clock.advance(elapsed, ticks.append)
        assert clock.steps == 30
        assert clock.remainder == pytest.approx(0, abs=1e-10)
        sequences.append(ticks)
    assert sequences[0] == sequences[1] == sequences[2]


@pytest.mark.parametrize("elapsed", [-1, nan, float("inf"), True, "bad"])
def test_invalid_frame_time_is_rejected(elapsed):
    with pytest.raises(ValueError):
        SimulationClock().advance(elapsed, lambda step: None)
