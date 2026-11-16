"""Manual 0/1 knapsack, greedy selection and discrete refuelling planning."""

from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from numbers import Real

from smart_racing.algorithms.sorting.rankings import merge_sort


@dataclass(frozen=True, slots=True)
class Pickup:
    id: int
    cost: int
    benefit: int

    def __post_init__(self):
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (self.id, self.cost, self.benefit)):
            raise ValueError("Pickup ID, cost and benefit must be integers")
        if self.cost < 0 or self.benefit < 0:
            raise ValueError("Pickup costs and benefits must be non-negative")


@dataclass(slots=True)
class Selection:
    items: list[Pickup]
    benefit: int
    cost: int
    states: int = 0


def knapsack(items: list[Pickup], budget: int, trace: list[dict] | None = None) -> Selection:
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
        raise ValueError("Budget must be a non-negative integer")
    if len({item.id for item in items}) != len(items):
        raise ValueError("Pickup IDs must be unique")
    table = [[0] * (budget + 1) for _ in range(len(items) + 1)]
    for index, item in enumerate(items, 1):
        for capacity in range(budget + 1):
            best = table[index - 1][capacity]
            if item.cost <= capacity:
                best = max(best, table[index - 1][capacity - item.cost] + item.benefit)
            table[index][capacity] = best
        if trace is not None:
            trace.append({"action": "dp row", "item": item.id, "value": table[index][budget],
                          "states": index * (budget + 1)})
    chosen = []
    capacity = budget
    for index in range(len(items), 0, -1):
        if table[index][capacity] != table[index - 1][capacity]:
            item = items[index - 1]
            chosen.append(item)
            capacity -= item.cost
    chosen.reverse()
    return Selection(chosen, table[-1][budget], sum(item.cost for item in chosen),
                     len(items) * (budget + 1))


def greedy(items: list[Pickup], budget: int, trace: list[dict] | None = None) -> Selection:
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
        raise ValueError("Budget must be a non-negative integer")
    if len({item.id for item in items}) != len(items):
        raise ValueError("Pickup IDs must be unique")
    ordered = merge_sort(items, key=lambda item: (
        0 if item.cost == 0 and item.benefit > 0 else 1,
        -Fraction(item.benefit, item.cost) if item.cost else 0,
        item.id,
    ))
    chosen = []
    spent = 0
    benefit = 0
    for item in ordered:
        if item.benefit and spent + item.cost <= budget:
            chosen.append(item)
            spent += item.cost
            benefit += item.benefit
        if trace is not None:
            trace.append({"action": "consider pickup", "item": item.id, "cost": spent,
                          "value": benefit})
    return Selection(chosen, benefit, spent)


def refuel_plan(distances: list[int], available: list[bool], initial_fuel: int,
                capacity: int = 100, max_purchase: int = 40,
                stop_time: int = 5) -> tuple[int, list[int]] | None:
    """Return minimum stop time and purchases for consecutive route segments.

    Each distance is a discrete fuel requirement; availability refers to the
    station at the beginning of the corresponding segment.
    """
    integers = [initial_fuel, capacity, max_purchase, *distances]
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in integers):
        raise ValueError("Fuel quantities must be non-negative integers")
    if any(not isinstance(value, bool) for value in available):
        raise ValueError("Station availability values must be boolean")
    if len(distances) != len(available) or not 0 <= initial_fuel <= capacity:
        raise ValueError("Invalid refuelling inputs")
    if isinstance(stop_time, bool) or not isinstance(stop_time, Real) or not isfinite(stop_time) or stop_time < 0:
        raise ValueError("Stop time must be finite and non-negative")
    states = {initial_fuel: (0, [])}
    for required, station in zip(distances, available):
        next_states = {}
        for fuel, (elapsed, purchases) in states.items():
            maximum = min(capacity - fuel, max_purchase) if station else 0
            for amount in range(maximum + 1):
                remaining = fuel + amount - required
                if remaining < 0:
                    continue
                candidate = (elapsed + (stop_time if amount else 0), purchases + [amount])
                if remaining not in next_states or candidate < next_states[remaining]:
                    next_states[remaining] = candidate
        states = next_states
        if not states:
            return None
    return min(states.values()) if states else None
