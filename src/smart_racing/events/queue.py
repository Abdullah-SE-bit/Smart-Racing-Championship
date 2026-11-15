"""Event queue ordered by simulation time, priority and insertion sequence."""

from dataclasses import dataclass
from math import isfinite
from numbers import Real

from smart_racing.algorithms.structures.heap import MinHeap


@dataclass(slots=True)
class Event:
    id: int
    time: float
    priority: int
    kind: str
    target: int
    duration: float = 0.0
    cancelled: bool = False
    insertion_sequence: int | None = None

    def __post_init__(self):
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (self.id, self.priority, self.target)):
            raise ValueError("Event ID, priority and target must be integers")
        if any(isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or value < 0
               for value in (self.time, self.duration)):
            raise ValueError("Event time and duration must be finite and non-negative")
        if not isinstance(self.kind, str) or not self.kind or not isinstance(self.cancelled, bool):
            raise ValueError("Event kind and cancellation state are invalid")
        if self.insertion_sequence is not None:
            raise ValueError("The event queue assigns the insertion sequence")


class EventQueue:
    def __init__(self):
        self.heap = MinHeap()
        self._sequence = 0
        self._events = {}
        self._used_ids = set()

    def schedule(self, event: Event):
        if event.id in self._used_ids or event.time < 0 or event.duration < 0:
            raise ValueError("Invalid or duplicate event")
        self._events[event.id] = event
        self._used_ids.add(event.id)
        event.insertion_sequence = self._sequence
        self.heap.push((event.time, event.priority, self._sequence, event.id))
        self._sequence += 1

    def cancel(self, event_id: int):
        self._events[event_id].cancelled = True

    def due(self, time: float):
        while self.heap and self.heap.peek()[0] <= time:
            _, _, _, event_id = self.heap.pop()
            event = self._events.pop(event_id)
            if not event.cancelled:
                yield event
