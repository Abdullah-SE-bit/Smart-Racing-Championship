"""Fixed-step simulation timing independent of rendering frame rate."""

from math import isfinite
from numbers import Real
from typing import Callable


class SimulationClock:
    def __init__(self, step: float = 1 / 30):
        if isinstance(step, bool) or not isinstance(step, Real) or not isfinite(step) or step <= 0:
            raise ValueError("Simulation step must be finite and positive")
        self.step = step
        self.remainder = 0.0
        self.steps = 0

    def advance(self, elapsed: float, tick: Callable[[float], None]) -> int:
        """Deliver whole fixed steps and retain fractional time for the next frame."""
        if isinstance(elapsed, bool) or not isinstance(elapsed, Real) or not isfinite(elapsed) or elapsed < 0:
            raise ValueError("Frame time must be finite and non-negative")
        self.remainder += elapsed
        count = 0
        while self.remainder + 1e-12 >= self.step:
            tick(self.step)
            self.remainder = max(0.0, self.remainder - self.step)
            self.steps += 1
            count += 1
        return count
