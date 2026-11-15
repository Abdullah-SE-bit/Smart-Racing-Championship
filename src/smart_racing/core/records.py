"""Stable, presentation-independent records produced by a race."""

from dataclasses import dataclass
from math import isfinite
from numbers import Real


@dataclass(frozen=True, slots=True)
class RaceResult:
    race_id: int
    racer_id: int
    finish_position: int
    finish_time: float | None
    fastest_lap: float | None
    bonus_points: int
    points_awarded: int
    finished: bool

    def __post_init__(self):
        for value in (self.race_id, self.racer_id, self.finish_position, self.bonus_points, self.points_awarded):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("Result identifiers, position and points must be integers")
        if self.finish_position < 1 or self.bonus_points < 0 or self.points_awarded < self.bonus_points:
            raise ValueError("Invalid result position or points")
        if not isinstance(self.finished, bool):
            raise ValueError("Finished must be boolean")
        for value in (self.finish_time, self.fastest_lap):
            if value is not None and (isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or value < 0):
                raise ValueError("Result times must be finite and non-negative")
        if self.finished != (self.finish_time is not None):
            raise ValueError("Only a finished racer has a finish time")
