"""Race points and the assignment's total championship ordering."""

from dataclasses import dataclass
from math import inf, isnan
from numbers import Real

from smart_racing.algorithms.sorting.rankings import merge_sort, top_k


POINTS = (25, 18, 15, 12, 10, 8, 6, 4, 2, 1)


@dataclass(slots=True)
class ChampionshipEntry:
    racer_id: int
    name: str
    total_points: int = 0
    wins: int = 0
    sum_positions: int = 0
    best_fastest_lap: float = inf

    def __post_init__(self):
        values = (self.racer_id, self.total_points, self.wins, self.sum_positions)
        if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
            raise ValueError("Championship IDs, points and counters must be integers")
        if self.total_points < 0 or self.wins < 0 or self.sum_positions < 0:
            raise ValueError("Championship points and counters cannot be negative")
        if (isinstance(self.best_fastest_lap, bool) or not isinstance(self.best_fastest_lap, Real)
                or isnan(self.best_fastest_lap) or self.best_fastest_lap < 0):
            raise ValueError("Best lap must be non-negative")


def ranking_key(entry: ChampionshipEntry):
    return (-entry.total_points, -entry.wins, entry.sum_positions,
            entry.best_fastest_lap, entry.racer_id)


def standings(entries: list[ChampionshipEntry]) -> list[ChampionshipEntry]:
    return merge_sort(entries, key=ranking_key)


def leaders(entries: list[ChampionshipEntry], k: int) -> list[ChampionshipEntry]:
    return top_k(entries, k, key=ranking_key)


def award_results(entries: list[ChampionshipEntry], results) -> None:
    by_id = {entry.racer_id: entry for entry in entries}
    for result in results:
        entry = by_id[result.racer_id]
        entry.total_points += result.points_awarded
        entry.wins += result.finished and result.finish_position == 1
        entry.sum_positions += result.finish_position
        if result.fastest_lap is not None:
            entry.best_fastest_lap = min(entry.best_fastest_lap, result.fastest_lap)
