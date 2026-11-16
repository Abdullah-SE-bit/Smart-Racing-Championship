"""Deterministic race simulation. This module has no Pygame dependency."""

from dataclasses import dataclass, field
from math import inf, isfinite
from numbers import Real

from smart_racing.algorithms.routing.shortest import shortest_path
from smart_racing.core.graph import CostProfile
from smart_racing.core.records import RaceResult
from smart_racing.championship.standings import POINTS
from smart_racing.events.queue import Event, EventQueue
from smart_racing.tracks.circuits import Circuit

EVENT_PRIORITIES = {
    "block": 1, "unblock": 1,
    "shortcut_close": 2, "shortcut_open": 2,
    "oil": 3, "clear_oil": 3,
    "restriction": 4, "clear_restriction": 4,
    "fuel_off": 5, "fuel_on": 5,
    "nitro_on": 6, "nitro_off": 6,
}


@dataclass(slots=True)
class Racer:
    id: int
    name: str
    strategy: str
    vertex: int
    fuel: float = 100.0
    nitro: int = 1
    next_checkpoint: int = 0
    laps: int = 0
    edge_id: int | None = None
    edge_target: int | None = None
    edge_progress: float = 0.0
    nitro_remaining: float = 0.0
    stop_remaining: float = 0.0
    lap_started: float = 0.0
    fastest_lap: float = inf
    total_time: float = 0.0
    finished: bool = False
    finish_time: float = inf
    dnf: bool = False
    desired_target: int | None = None
    refuelled_here: bool = False
    status: str = "ready"
    visited_since_checkpoint: set[int] = field(default_factory=set)
    detour: list[int] = field(default_factory=list)

    def __post_init__(self):
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (self.id, self.vertex, self.nitro, self.next_checkpoint, self.laps)):
            raise ValueError("Racer ID, vertex and counters must be integers")
        if not isinstance(self.name, str) or not self.name.strip() or self.strategy not in {"human", "main", "shortcut", "distance"}:
            raise ValueError("Invalid racer name or strategy")
        if (isinstance(self.fuel, bool) or not isinstance(self.fuel, Real) or not isfinite(self.fuel)
                or not 0 <= self.fuel <= 100 or not 0 <= self.nitro <= 3):
            raise ValueError("Invalid racer fuel or nitro")
        if self.next_checkpoint < 0 or self.laps < 0 or (self.finished and self.dnf):
            raise ValueError("Invalid racer progress")


@dataclass(slots=True)
class Race:
    circuit: Circuit
    laps_required: int = 2
    time_limit: float = 240.0
    elapsed: float = 0.0
    racers: list[Racer] = field(default_factory=list)
    events: EventQueue = field(default_factory=EventQueue)
    event_log: list[str] = field(default_factory=list)
    active_effects: dict[int, Event] = field(default_factory=dict)
    service_active: dict[int, bool] = field(default_factory=dict)
    collected_pickups: set[int] = field(default_factory=set)
    _initial_status: dict[int, str] = field(default_factory=dict)
    _initial_difficulty: dict[int, int] = field(default_factory=dict)
    _initial_service: dict[int, bool] = field(default_factory=dict)
    _fixed_detours: dict[tuple[int, int], list[int]] = field(default_factory=dict)
    _next_expiry_id: int = -1

    def __post_init__(self):
        if (isinstance(self.laps_required, bool) or not isinstance(self.laps_required, int) or self.laps_required < 1
                or isinstance(self.time_limit, bool) or not isinstance(self.time_limit, Real)
                or not isfinite(self.time_limit) or self.time_limit <= 0
                or isinstance(self.elapsed, bool) or not isinstance(self.elapsed, Real)
                or not isfinite(self.elapsed) or not 0 <= self.elapsed <= self.time_limit):
            raise ValueError("Invalid race duration")
        if not self.racers:
            self.racers = [Racer(0, "YOU", "human", self.circuit.start),
                           Racer(1, "NOVA", "main", self.circuit.start),
                           Racer(2, "BLAZE", "shortcut", self.circuit.start),
                           Racer(3, "VECTOR", "distance", self.circuit.start)]
        if len({racer.id for racer in self.racers}) != len(self.racers):
            raise ValueError("Racer IDs must be unique")
        if any(racer.vertex not in self.circuit.graph.vertices for racer in self.racers):
            raise ValueError("Racer start vertex must exist")
        self._initial_status = {edge.id: edge.status for edge in self.circuit.graph.edges.values()}
        self._initial_difficulty = {edge.id: edge.difficulty for edge in self.circuit.graph.edges.values()}
        self.service_active = {v.id: v.active for v in self.circuit.graph.vertices.values()}
        self._initial_service = self.service_active.copy()
        for racer in self.racers:
            racer.visited_since_checkpoint.add(racer.vertex)
        self._prepare_detours()

    def _prepare_detours(self):
        graph = self.circuit.graph
        distance = CostProfile(distance=1, time=0, fuel=0, difficulty=0, obstacle=0)
        progress = 0
        for source, target in zip(self.circuit.main_route, self.circuit.main_route[1:]):
            if progress < len(self.circuit.checkpoints) and source == self.circuit.checkpoints[progress]:
                progress += 1
            road = next((edge for neighbor, edge in graph.neighbors(source) if neighbor == target), None)
            if road is None:
                continue
            old_status = road.status
            road.status = "blocked"
            try:
                # Main routes can contain service/intersection vertices between
                # checkpoints, so route position is not checkpoint progress.
                future = set(self.circuit.checkpoints[progress:]) - {target}
                route = shortest_path(graph, source, target, distance, avoid_vertices=future)
                self._fixed_detours[(source, target)] = route.vertices[1:]
            finally:
                road.status = old_status

    @property
    def over(self):
        return self.elapsed >= self.time_limit or all(r.finished or r.dnf for r in self.racers)

    def options(self, racer: Racer):
        return list(self.circuit.graph.neighbors(racer.vertex))

    def _racer_by_id(self, racer_id: int) -> Racer:
        for racer in self.racers:
            if racer.id == racer_id:
                return racer
        raise ValueError(f"Unknown racer ID {racer_id}")

    def choose(self, racer_id: int, target: int):
        racer = self._racer_by_id(racer_id)
        if racer.strategy != "human" or racer.edge_id is not None or racer.finished or racer.dnf:
            return False
        if target not in [neighbor for neighbor, _ in self.options(racer)]:
            return False
        racer.desired_target = target
        return True

    def activate_nitro(self, racer_id: int):
        racer = self._racer_by_id(racer_id)
        if racer.nitro > 0 and racer.nitro_remaining <= 0 and not racer.finished and not racer.dnf:
            racer.nitro -= 1
            racer.nitro_remaining = 4.0
            self.event_log.append(f"{racer.name}: nitro activated")
            return True
        return False

    def refuel(self, racer_id: int):
        racer = self._racer_by_id(racer_id)
        vertex = self.circuit.graph.vertices[racer.vertex]
        if (racer.edge_id is not None or racer.refuelled_here or racer.finished or racer.dnf
                or vertex.kind != "fuel" or not self.service_active[vertex.id] or racer.fuel >= 100):
            return False
        racer.fuel = min(100.0, racer.fuel + 40.0)
        racer.stop_remaining = 3.0
        racer.refuelled_here = True
        racer.status = "refuelling"
        self.event_log.append(f"{racer.name}: refuelling")
        return True

    def schedule(self, event: Event):
        if event.id < 0:
            raise ValueError("Negative event IDs are reserved for expiration events")
        road_kinds = {"block", "unblock", "restriction", "clear_restriction", "oil", "clear_oil", "shortcut_close", "shortcut_open"}
        service_kinds = {"fuel_off", "fuel_on", "nitro_on", "nitro_off"}
        if event.kind in road_kinds and event.target not in self.circuit.graph.edges:
            raise ValueError("Unknown road")
        if event.kind in service_kinds and event.target not in self.circuit.graph.vertices:
            raise ValueError("Unknown service")
        if event.kind in service_kinds:
            expected = "fuel" if event.kind.startswith("fuel") else "nitro"
            if self.circuit.graph.vertices[event.target].kind != expected:
                raise ValueError("Event targets the wrong service type")
        if event.kind in {"shortcut_close", "shortcut_open"} and not self.circuit.graph.edges[event.target].shortcut:
            raise ValueError("Target road is not a shortcut")
        if event.kind not in road_kinds | service_kinds:
            raise ValueError("Unknown event type")
        if event.priority != EVENT_PRIORITIES[event.kind]:
            raise ValueError("Event priority does not match its type")
        self.events.schedule(event)

    def _refresh_effects(self):
        graph = self.circuit.graph
        for edge_id, status in self._initial_status.items():
            relevant = [effect for effect in self.active_effects.values() if effect.target == edge_id]
            graph.edges[edge_id].status = ("blocked" if any(e.kind in {"block", "shortcut_close"} for e in relevant)
                                           else "restricted" if any(e.kind in {"restriction", "oil"} for e in relevant)
                                           else "open" if any(e.kind == "shortcut_open" for e in relevant)
                                           else status)
            graph.edges[edge_id].difficulty = min(5, self._initial_difficulty[edge_id]
                                                 + int(any(e.kind == "oil" for e in relevant)))
        for vertex in graph.vertices.values():
            effects = [e for e in self.active_effects.values() if e.target == vertex.id]
            active = self._initial_service[vertex.id]
            for effect in effects:
                if effect.kind in {"fuel_off", "nitro_off"}:
                    active = False
                elif effect.kind in {"fuel_on", "nitro_on"}:
                    active = True
            self.service_active[vertex.id] = active and vertex.id not in self.collected_pickups

    def _process_events(self):
        changed = False
        for event in self.events.due(self.elapsed + 1e-9):
            changed = True
            if event.kind == "_expire":
                self.active_effects.pop(event.target, None)
                continue
            if event.kind == "nitro_on":
                self.collected_pickups.discard(event.target)
            if event.kind in {"unblock", "clear_restriction", "clear_oil"}:
                kind = {"unblock": "block", "clear_restriction": "restriction", "clear_oil": "oil"}[event.kind]
                self.active_effects = {key: effect for key, effect in self.active_effects.items()
                                       if not (effect.kind == kind and effect.target == event.target)}
                if event.kind == "unblock":
                    self._initial_status[event.target] = "open"
            elif not event.duration and event.kind in {"block", "shortcut_close", "shortcut_open"}:
                self._initial_status[event.target] = "open" if event.kind == "shortcut_open" else "blocked"
            elif not event.duration and event.kind in {"fuel_off", "fuel_on", "nitro_off", "nitro_on"}:
                self._initial_service[event.target] = event.kind in {"fuel_on", "nitro_on"}
            else:
                self.active_effects[event.id] = event
                if event.duration:
                    expiry = Event(self._next_expiry_id, event.time + event.duration,
                                   event.priority, "_expire", event.id)
                    self._next_expiry_id -= 1
                    self.events.schedule(expiry)
            self.event_log.append(f"{self.elapsed:.1f}s: {event.kind.replace('_', ' ')} on {event.target}")
        if changed:
            self._refresh_effects()

    def _destination(self, racer):
        if racer.next_checkpoint < len(self.circuit.checkpoints):
            return self.circuit.checkpoints[racer.next_checkpoint]
        return self.circuit.start

    def _shortcut_detour(self, racer, target, future):
        """Find a deterministic, legal route to and across a useful shortcut.

        Each candidate must reach the next checkpoint without passing a later
        checkpoint or revisiting a vertex in this checkpoint leg. The racer
        commits only through the shortcut and then makes its normal decision.
        """
        graph = self.circuit.graph
        distance = CostProfile(distance=1, time=0, fuel=0, difficulty=0, obstacle=0)
        visited = racer.visited_since_checkpoint - {racer.vertex}
        candidates = []
        for source in sorted(graph.vertices):
            if source in future or source in visited or (source == target and source != racer.vertex):
                continue
            approach = shortest_path(graph, racer.vertex, source, distance,
                                     avoid_vertices=future | visited | ({target} if source != target else set()))
            if not approach.vertices:
                continue
            for destination, edge in graph.neighbors(source):
                if not edge.shortcut or destination in future:
                    continue
                if destination in (set(approach.vertices) | visited) and destination != target:
                    continue
                avoid = future | visited | (set(approach.vertices) - {destination})
                exit_route = shortest_path(graph, destination, target, distance, avoid_vertices=avoid)
                if not exit_route.vertices:
                    continue
                fuel = sum(graph.edges[edge_id].fuel_cost * (1 + .1 * (graph.edges[edge_id].difficulty - 1))
                           for edge_id in approach.edges + [edge.id] + exit_route.edges)
                if fuel > racer.fuel + 1e-9:
                    continue
                path = approach.vertices[1:] + [destination]
                candidates.append((approach.cost, edge.id, source, destination, path))
        return min(candidates)[-1] if candidates else []

    def _ai_target(self, racer):
        graph = self.circuit.graph
        target = self._destination(racer)
        if racer.fuel < 25 and racer.strategy == "distance":
            distance_profile = CostProfile(distance=1, time=0, fuel=0, difficulty=0, obstacle=0)
            future = set(self.circuit.checkpoints[racer.next_checkpoint + 1:])
            route = shortest_path(graph, racer.vertex, target, distance_profile, avoid_vertices=future)
            fuel_needed = 0.0
            for index, edge_id in enumerate(route.edges):
                edge = graph.edges[edge_id]
                fuel_needed += edge.fuel_cost * (1 + .1 * (edge.difficulty - 1))
                vertex = graph.vertices[route.vertices[index + 1]]
                if fuel_needed > racer.fuel + 1e-9:
                    break
                if vertex.kind == "fuel" and self.service_active[vertex.id]:
                    racer.detour.clear()
                    return route.vertices[1]
        elif racer.fuel < 25:
            # Search active stations that can be reached on the remaining fuel.
            fuel_profile = CostProfile(distance=0, time=0, fuel=1, difficulty=0, obstacle=0,
                                       fuel_reference=1)
            # A station detour must not route through a checkpoint that has not
            # become eligible yet; the normal opponent routes obey this too.
            future = set(self.circuit.checkpoints[racer.next_checkpoint + 1:])
            candidates = []
            for vertex in graph.vertices.values():
                if vertex.kind != "fuel" or not self.service_active[vertex.id] or vertex.id == racer.vertex:
                    continue
                route = shortest_path(graph, racer.vertex, vertex.id, fuel_profile,
                                      avoid_vertices=future)
                if route.vertices and route.cost <= racer.fuel:
                    candidates.append((route.cost, vertex.id, route.vertices[1]))
            if candidates:
                racer.detour.clear()
                return min(candidates, key=lambda candidate: candidate[1])[2]
        if racer.detour:
            next_vertex = racer.detour[0]
            if all(any(n == destination for n, _ in graph.neighbors(source))
                   for source, destination in zip([racer.vertex] + racer.detour, racer.detour)):
                return next_vertex
            racer.detour.clear()
        distance = CostProfile(distance=1, time=0, fuel=0, difficulty=0, obstacle=0)
        future = set(self.circuit.checkpoints[racer.next_checkpoint + 1:])
        avoid = future | (racer.visited_since_checkpoint - {racer.vertex, target})
        if racer.strategy == "shortcut":
            shortcut = self._shortcut_detour(racer, target, future)
            if shortcut:
                racer.detour = shortcut
                return shortcut[0]
        if racer.strategy in {"main", "shortcut"} and racer.vertex in self.circuit.main_route[:-1]:
            index = self.circuit.main_route.index(racer.vertex)
            next_vertex = self.circuit.main_route[index + 1]
            if next_vertex not in future and next_vertex in [n for n, _ in graph.neighbors(racer.vertex)]:
                return next_vertex
            detour = self._fixed_detours.get((racer.vertex, next_vertex), [])
            if detour and any(n == detour[0] for n, _ in graph.neighbors(racer.vertex)):
                racer.detour = detour.copy()
                return racer.detour[0]
            return None
        route = shortest_path(graph, racer.vertex, target, distance, avoid_vertices=avoid)
        if not route.vertices:
            # A closure or dead end may make revisiting a road necessary.
            racer.visited_since_checkpoint = {racer.vertex}
            route = shortest_path(graph, racer.vertex, target, distance, avoid_vertices=future)
        return route.vertices[1] if len(route.vertices) > 1 else None

    def _enter(self, racer, target, nitro_remaining):
        road = next((edge for neighbor, edge in self.options(racer) if neighbor == target), None)
        if road is None:
            return
        needed = road.fuel_cost * (1 + .1 * (road.difficulty - 1))
        duration = max(road.base_time, 0.01) * (1.5 if road.status == "restricted" else 1.0)
        boosted_fraction = min(1.0, nitro_remaining * 1.5 / duration)
        if racer.fuel + 1e-9 < needed * (1 + boosted_fraction):
            affordable = any(edge.fuel_cost * (1 + .1 * (edge.difficulty - 1)) <= racer.fuel
                             for _, edge in self.options(racer))
            vertex = self.circuit.graph.vertices[racer.vertex]
            can_refuel = vertex.kind == "fuel" and self.service_active[vertex.id] and not racer.refuelled_here
            if not affordable and not can_refuel:
                racer.dnf = True
                racer.status = "out of fuel"
                self.event_log.append(f"{racer.name}: out of fuel")
            else:
                racer.status = "insufficient fuel for selected road"
            return
        racer.edge_id, racer.edge_target, racer.edge_progress = road.id, target, 0.0
        racer.status = "racing"

    def _arrive(self, racer):
        racer.vertex = racer.edge_target
        racer.visited_since_checkpoint.add(racer.vertex)
        if racer.detour and racer.detour[0] == racer.vertex:
            racer.detour.pop(0)
        racer.edge_id = racer.edge_target = None
        racer.edge_progress = 0.0
        racer.refuelled_here = False
        target = self._destination(racer)
        if racer.vertex == target:
            if racer.next_checkpoint < len(self.circuit.checkpoints):
                racer.next_checkpoint += 1
                racer.visited_since_checkpoint = {racer.vertex}
            else:
                racer.laps += 1
                racer.fastest_lap = min(racer.fastest_lap, self.elapsed - racer.lap_started)
                racer.lap_started = self.elapsed
                racer.next_checkpoint = 0
                racer.visited_since_checkpoint = {racer.vertex}
                if racer.laps >= self.laps_required:
                    racer.finished = True
                    racer.finish_time = self.elapsed
                    racer.status = "finished"
                    self.event_log.append(f"{racer.name}: finished")
        vertex = self.circuit.graph.vertices[racer.vertex]
        if vertex.kind == "fuel" and racer.strategy != "human" and racer.fuel < 25:
            self.refuel(racer.id)
        if vertex.kind == "nitro" and self.service_active[vertex.id] and racer.nitro < 3:
            racer.nitro += 1
            self.service_active[vertex.id] = False
            self.collected_pickups.add(vertex.id)
            self.event_log.append(f"{racer.name}: collected nitro")

    def tick(self, delta: float):
        if isinstance(delta, bool) or not isinstance(delta, Real) or not isfinite(delta):
            raise ValueError("Simulation delta must be a finite number")
        if delta <= 0 or self.over:
            return
        delta = min(delta, self.time_limit - self.elapsed)
        self.elapsed += delta
        self._process_events()
        for racer in self.racers:
            if racer.finished or racer.dnf:
                continue
            racer.total_time += delta
            nitro_remaining = racer.nitro_remaining
            boost_time = min(delta, nitro_remaining)
            racer.nitro_remaining = max(0.0, nitro_remaining - delta)
            if racer.stop_remaining > 0:
                racer.stop_remaining = max(0.0, racer.stop_remaining - delta)
                continue
            if racer.edge_id is None:
                target = racer.desired_target if racer.strategy == "human" else self._ai_target(racer)
                racer.desired_target = None
                if target is not None:
                    self._enter(racer, target, nitro_remaining)
                elif racer.strategy != "human":
                    if racer.status != "waiting for a route":
                        self.event_log.append(f"{racer.name}: waiting for a route")
                    racer.status = "waiting for a route"
            if racer.edge_id is not None:
                road = self.circuit.graph.edges[racer.edge_id]
                duration = max(road.base_time, 0.01) * (1.5 if road.status == "restricted" else 1.0)
                remaining = 1.0 - racer.edge_progress
                boosted_progress = min(remaining, boost_time * 1.5 / duration)
                normal_progress = min(remaining - boosted_progress, (delta - boost_time) / duration)
                progress = boosted_progress + normal_progress
                fuel = (normal_progress + 2 * boosted_progress) * road.fuel_cost * (1 + .1 * (road.difficulty - 1))
                if fuel > racer.fuel + 1e-9:
                    racer.fuel = 0
                    racer.dnf = True
                    racer.status = "out of fuel"
                    continue
                racer.fuel = max(0.0, racer.fuel - fuel)
                racer.edge_progress += progress
                if racer.edge_progress >= 1.0 - 1e-9:
                    self._arrive(racer)

    def results(self):
        return sorted(self.racers, key=lambda r: (0 if r.finished else 1,
                      r.finish_time if r.finished else -r.laps,
                      0 if r.finished else -r.next_checkpoint,
                      0 if r.finished else r.total_time, r.id))

    def result_records(self, race_id: int) -> list[RaceResult]:
        if not self.over:
            raise ValueError("Race results are available when the race ends")
        records = []
        for position, racer in enumerate(self.results(), 1):
            points = POINTS[position - 1] if racer.finished and position <= len(POINTS) else 0
            records.append(RaceResult(race_id, racer.id, position,
                                      racer.finish_time if racer.finished else None,
                                      racer.fastest_lap if isfinite(racer.fastest_lap) else None,
                                      0, points, racer.finished))
        return records
