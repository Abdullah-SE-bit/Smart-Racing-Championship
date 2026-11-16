from copy import deepcopy
from pathlib import Path

import pytest

from smart_racing.algorithms.routing.shortest import shortest_path
from smart_racing.championship.standings import ChampionshipEntry, award_results, leaders, standings
from smart_racing.events.queue import Event, EventQueue
from smart_racing.core.graph import Edge, Graph, Vertex
from smart_racing.game.race import Race, Racer
from smart_racing.tracks.circuits import Circuit, load_circuit, validate_circuit
from smart_racing.tracks.generator import generate_circuit


CIRCUITS = sorted(Path("data/circuits").glob("*.json"))


def test_three_authored_circuits_have_required_topology():
    assert len(CIRCUITS) == 3
    topologies = set()
    for path in CIRCUITS:
        circuit = load_circuit(path)
        assert not validate_circuit(circuit)
        assert len(circuit.checkpoints) == 10
        assert sum(edge.shortcut for edge in circuit.graph.edges.values()) >= 2
        assert len({edge.difficulty for edge in circuit.graph.edges.values()}) > 1
        topologies.add(frozenset((min(edge.source, edge.target), max(edge.source, edge.target), edge.directed)
                                 for edge in circuit.graph.edges.values()))
    assert len(topologies) == 3


def test_validator_rejects_single_ordered_lap_and_infeasible_fuel():
    circuit = load_circuit(CIRCUITS[0])
    main_pairs = {frozenset((a, b)) for a, b in zip(circuit.main_route, circuit.main_route[1:])}
    single_lap = deepcopy(circuit)
    for edge in single_lap.graph.edges.values():
        if frozenset((edge.source, edge.target)) not in main_pairs and 13 not in (edge.source, edge.target):
            edge.status = "blocked"
    assert any("two simple ordered" in error for error in validate_circuit(single_lap))
    fuel_impossible = deepcopy(circuit)
    for edge in fuel_impossible.graph.edges.values():
        edge.fuel_cost = 101
    assert any("fuel plan" in error for error in validate_circuit(fuel_impossible))


def test_validator_reports_unknown_main_route_vertex():
    circuit = load_circuit(CIRCUITS[0])
    circuit.main_route.insert(1, 99999)
    assert "main route contains a nonexistent vertex" in validate_circuit(circuit)


def test_event_order_cancellation_and_independent_expiration():
    queue = EventQueue()
    queue.schedule(Event(1, 1, 2, "block", 0))
    queue.schedule(Event(2, 1, 1, "block", 0))
    queue.schedule(Event(3, 1, 1, "block", 0))
    queue.cancel(2)
    assert [event.id for event in queue.due(1)] == [3, 1]
    with pytest.raises(ValueError, match="duplicate"):
        queue.schedule(Event(1, 2, 1, "block", 0))
    race = Race(load_circuit(CIRCUITS[0]))
    race.schedule(Event(4, 1, 1, "block", 0, 2))
    race.schedule(Event(5, 1, 1, "block", 0, 5))
    race.tick(1)
    assert race.circuit.graph.edges[0].status == "blocked"
    race.tick(2)
    assert race.circuit.graph.edges[0].status == "blocked"
    race.tick(3)
    assert race.circuit.graph.edges[0].status == "open"


def play(seedless_circuit):
    race = Race(load_circuit(seedless_circuit), laps_required=2)
    race.schedule(Event(100, 10, 1, "block", 8, 8))
    for _ in range(10000):
        human = race.racers[0]
        if human.edge_id is None and not human.finished and not human.dnf:
            target = race._destination(human)
            route = shortest_path(race.circuit.graph, human.vertex, target)
            if len(route.vertices) > 1:
                race.choose(0, route.vertices[1])
        race.tick(.1)
        if race.over:
            break
    return race


@pytest.mark.parametrize("circuit_path", CIRCUITS)
def test_complete_deterministic_race_and_championship(circuit_path):
    race = play(circuit_path)
    second = play(circuit_path)
    assert race.over
    assert all(racer.finished for racer in race.racers)
    assert [(r.id, r.finish_time) for r in race.results()] == [(r.id, r.finish_time) for r in second.results()]
    entries = [ChampionshipEntry(r.id, r.name) for r in race.racers]
    award_results(entries, race.result_records(1))
    assert standings(entries)[0].total_points == 25
    assert leaders(entries, 3) == standings(entries)[:3]


def test_refuelling_and_nitro_duration_are_consistent():
    race = Race(load_circuit(CIRCUITS[0]))
    human = race.racers[0]
    human.vertex = 11
    human.fuel = 70
    assert race.refuel(0)
    assert human.fuel == 100 and human.stop_remaining == 3
    assert race.event_log[-1] == "YOU: refuelling"
    assert not race.refuel(0)
    assert race.activate_nitro(0)
    assert race.event_log[-1] == "YOU: nitro activated"
    race.tick(1)
    assert human.nitro_remaining == 3


def test_nitro_pickup_respects_capacity_and_is_consumed_on_collection():
    graph = Graph()
    for vertex in (Vertex(0, 0, 0, "start"), Vertex(1, 1, 0, "nitro"),
                   Vertex(2, 2, 0, "checkpoint", 1)):
        graph.add_vertex(vertex)
    graph.add_edge(Edge(0, 0, 1, 1, 1, 1))
    graph.add_edge(Edge(1, 0, 2, 1, 1, 1))
    racer = Racer(0, "Human", "human", 0, nitro=3)
    race = Race(Circuit("Pickup", graph, 0, [2], [0, 2, 0]), racers=[racer])
    assert race.choose(0, 1)
    race.tick(1)
    assert racer.nitro == 3 and race.service_active[1]
    assert race.choose(0, 0)
    race.tick(1)
    racer.nitro = 2
    assert race.choose(0, 1)
    race.tick(1)
    assert racer.nitro == 3 and not race.service_active[1]
    assert 1 in race.collected_pickups
    assert race.event_log[-1] == "Human: collected nitro"


@pytest.mark.parametrize("strategy", ["human", "main", "shortcut", "distance"])
def test_refuelling_rules_are_shared_by_all_strategies(strategy):
    circuit = load_circuit(CIRCUITS[0])
    racer = Racer(9, "Driver", strategy, 11, fuel=99)
    race = Race(circuit, racers=[racer])
    race.service_active[11] = False
    assert not race.refuel(9)
    race.service_active[11] = True
    assert race.refuel(9)
    assert racer.fuel == 100 and racer.stop_remaining == 3
    assert not race.refuel(9)


def test_nitro_boost_charges_only_the_affected_road_portion():
    graph = Graph()
    graph.add_vertex(Vertex(0, 0, 0, "start"))
    graph.add_vertex(Vertex(1, 1, 0, "checkpoint", 1))
    graph.add_edge(Edge(0, 0, 1, 1, 4, 10, difficulty=3))
    circuit = Circuit("Fuel fixture", graph, 0, [1], [0, 1, 0])
    ordinary = Race(deepcopy(circuit), racers=[Racer(17, "Normal", "human", 0)])
    boosted = Race(deepcopy(circuit), racers=[Racer(42, "Boosted", "human", 0)])
    assert ordinary.choose(17, 1)
    assert boosted.choose(42, 1)
    assert boosted.activate_nitro(42)
    ordinary.tick(1)
    boosted.tick(1)
    assert ordinary.racers[0].fuel == pytest.approx(97)
    assert boosted.racers[0].fuel == pytest.approx(91)
    assert ordinary.racers[0].edge_progress == pytest.approx(.25)
    assert boosted.racers[0].edge_progress == pytest.approx(.375)


def test_expired_and_overlapping_road_effects_restore_correctly():
    race = Race(load_circuit(CIRCUITS[0]))
    original = race.circuit.graph.edges[0].difficulty
    race.schedule(Event(1, 1, 3, "oil", 0, 5))
    race.schedule(Event(2, 1, 4, "restriction", 0, 3))
    race.tick(1)
    assert race.circuit.graph.edges[0].status == "restricted"
    assert race.circuit.graph.edges[0].difficulty == min(5, original + 1)
    race.tick(3)
    assert race.circuit.graph.edges[0].difficulty == min(5, original + 1)
    race.tick(2)
    assert race.circuit.graph.edges[0].status == "open"
    assert race.circuit.graph.edges[0].difficulty == original


def test_permanent_road_and_service_events_can_be_reversed():
    race = Race(load_circuit(CIRCUITS[0]))
    shortcut = next(edge.id for edge in race.circuit.graph.edges.values() if edge.shortcut)
    race.schedule(Event(1, 1, 2, "shortcut_close", shortcut))
    race.schedule(Event(2, 2, 2, "shortcut_open", shortcut))
    race.schedule(Event(3, 1, 5, "fuel_off", 11))
    race.schedule(Event(4, 2, 5, "fuel_on", 11))
    race.tick(1)
    assert race.circuit.graph.edges[shortcut].status == "blocked"
    assert not race.service_active[11]
    race.tick(1)
    assert race.circuit.graph.edges[shortcut].status == "open"
    assert race.service_active[11]
    with pytest.raises(ValueError, match="wrong service"):
        race.schedule(Event(5, 3, 5, "fuel_off", 12))


def test_simultaneous_events_use_assignment_priorities_before_movement():
    race = Race(load_circuit(CIRCUITS[0]))
    shortcut = next(edge.id for edge in race.circuit.graph.edges.values() if edge.shortcut)
    for event in (Event(6, 1, 6, "nitro_on", 12, 2), Event(3, 1, 3, "oil", 4, 2),
                  Event(5, 1, 5, "fuel_off", 11, 2), Event(2, 1, 2, "shortcut_close", shortcut, 2),
                  Event(4, 1, 4, "restriction", 5, 2), Event(1, 1, 1, "block", 0, 2)):
        race.schedule(event)
    race.tick(1)
    assert [message.split(": ", 1)[1].rsplit(" on ", 1)[0] for message in race.event_log[:6]] == [
        "block", "shortcut close", "oil", "restriction", "fuel off", "nitro on"]
    assert race.circuit.graph.edges[0].status == "blocked"
    with pytest.raises(ValueError, match="priority"):
        race.schedule(Event(7, 2, 6, "block", 0))


def test_shortcut_opponent_uses_service_detour_and_falls_back_when_closed():
    race = Race(load_circuit(CIRCUITS[0]))
    opponent = race.racers[2]
    opponent.vertex = 2
    opponent.next_checkpoint = 2
    opponent.visited_since_checkpoint = {2}
    assert race._ai_target(opponent) == 11
    shortcut = next(edge for neighbor, edge in race.circuit.graph.neighbors(11) if neighbor == 3)
    shortcut.status = "blocked"
    assert race._ai_target(opponent) == 3


def test_main_route_opponent_uses_fixed_detour_and_waits_if_it_closes():
    race = Race(load_circuit(CIRCUITS[0]))
    opponent = race.racers[1]
    opponent.vertex = 2
    opponent.next_checkpoint = 2
    opponent.visited_since_checkpoint = {2}
    main_road = next(edge for neighbor, edge in race.circuit.graph.neighbors(2) if neighbor == 3)
    main_road.status = "blocked"
    assert race._ai_target(opponent) == 11
    opponent.vertex = 11
    opponent.detour.pop(0)
    detour_road = next(edge for neighbor, edge in race.circuit.graph.neighbors(11) if neighbor == 3)
    detour_road.status = "blocked"
    assert race._ai_target(opponent) is None


def test_fixed_detour_avoids_checkpoints_before_intermediate_service():
    graph = Graph()
    for vertex in (Vertex(0, 0, 0, "start"), Vertex(1, 1, 0, "checkpoint", 1),
                   Vertex(2, 2, 0, "checkpoint", 2), Vertex(10, 1, 1, "fuel"),
                   Vertex(11, 0, 1, "intersection")):
        graph.add_vertex(vertex)
    for edge in (Edge(0, 0, 10, 1, 1, 1), Edge(1, 10, 1, 1, 1, 1),
                 Edge(2, 1, 2, 1, 1, 1), Edge(3, 2, 0, 1, 1, 1),
                 Edge(4, 0, 1, 1, 1, 1), Edge(5, 0, 11, 3, 1, 1),
                 Edge(6, 11, 10, 3, 1, 1)):
        graph.add_edge(edge)
    race = Race(Circuit("Detour", graph, 0, [1, 2], [0, 10, 1, 2, 0]))
    assert race._fixed_detours[(0, 10)] == [11, 10]


def test_distance_opponent_only_seeks_reachable_station_on_its_route():
    race = Race(load_circuit(CIRCUITS[0]))
    opponent = race.racers[3]
    opponent.vertex = 2
    opponent.next_checkpoint = 2
    opponent.visited_since_checkpoint = {2}
    opponent.fuel = 20
    assert race._ai_target(opponent) == 3
    main_road = next(edge for neighbor, edge in race.circuit.graph.neighbors(2) if neighbor == 3)
    main_road.status = "blocked"
    assert race._ai_target(opponent) == 11


@pytest.mark.parametrize("strategy", ["main", "shortcut"])
def test_low_fuel_station_detour_does_not_cross_future_checkpoint(strategy):
    graph = Graph()
    for vertex in (Vertex(0, 0, 0, "start"), Vertex(1, 1, 0, "checkpoint", 1),
                   Vertex(2, 2, 0, "checkpoint", 2), Vertex(3, 0, 1, "fuel")):
        graph.add_vertex(vertex)
    graph.add_edge(Edge(0, 0, 1, 1, 1, 1))
    graph.add_edge(Edge(1, 0, 2, 1, 1, 1))
    graph.add_edge(Edge(2, 2, 3, 1, 1, 1))
    circuit = Circuit("Future checkpoint", graph, 0, [1, 2], [0, 1])
    racer = Racer(1, "Opponent", strategy, 0, fuel=20)
    race = Race(circuit, racers=[racer])
    # The only station route crosses checkpoint 2 before checkpoint 1.
    # Follow the legal main route instead of taking that station detour.
    assert race._ai_target(racer) == 1


@pytest.mark.parametrize("strategy", ["main", "shortcut"])
def test_low_fuel_opponent_uses_first_eligible_station_by_stable_id(strategy):
    graph = Graph()
    for vertex in (Vertex(0, 0, 0, "start"), Vertex(1, 1, 0, "checkpoint", 1),
                   Vertex(2, 2, 0, "checkpoint", 2), Vertex(5, 0, 1, "fuel"),
                   Vertex(9, 0, 2, "fuel")):
        graph.add_vertex(vertex)
    for edge in (Edge(0, 0, 1, 1, 1, 1), Edge(1, 1, 2, 1, 1, 1),
                 Edge(2, 2, 0, 1, 1, 1), Edge(3, 0, 5, 1, 1, 1),
                 Edge(4, 0, 9, 1, 1, 1)):
        graph.add_edge(edge)
    racer = Racer(1, "Opponent", strategy, 0, fuel=20)
    race = Race(Circuit("Stations", graph, 0, [1, 2], [0, 1, 2, 0]), racers=[racer])
    assert race._ai_target(racer) == 5
    race.tick(1)
    assert racer.vertex == 5 and racer.stop_remaining == 3
    assert racer.fuel == pytest.approx(59)


def test_seed_and_events_reproduce_opponent_decisions_each_tick():
    def replay():
        circuit = generate_circuit(42)
        race = Race(circuit)
        road = sorted(circuit.graph.edges)[8]
        race.schedule(Event(1, 2, 1, "block", road, 3))
        snapshots = []
        for _ in range(150):
            human = race.racers[0]
            if human.edge_id is None and not human.finished and not human.dnf:
                future = set(circuit.checkpoints[human.next_checkpoint + 1:])
                route = shortest_path(circuit.graph, human.vertex, race._destination(human),
                                      avoid_vertices=future)
                if len(route.vertices) > 1:
                    race.choose(human.id, route.vertices[1])
            race.tick(.1)
            snapshots.append([(racer.vertex, racer.edge_id, racer.edge_target, racer.edge_progress,
                               racer.fuel, racer.next_checkpoint, racer.laps, racer.status)
                              for racer in race.racers])
        return snapshots, race.event_log

    assert replay() == replay()


def test_race_ties_and_unfinished_order_use_the_required_keys():
    race = Race(load_circuit(CIRCUITS[0]))
    first, second, third, fourth = race.racers
    first.finished = second.finished = True
    first.finish_time = second.finish_time = 12.0
    third.dnf = fourth.dnf = True
    third.laps = fourth.laps = 1
    third.next_checkpoint = fourth.next_checkpoint = 3
    third.total_time, fourth.total_time = 30, 20
    assert [racer.id for racer in race.results()] == [0, 1, 3, 2]
    records = race.result_records(1)
    assert [record.points_awarded for record in records] == [25, 18, 0, 0]


def test_full_ten_racer_points_table():
    racers = [Racer(index, f"Racer {index}", "human", 0) for index in range(10)]
    race = Race(load_circuit(CIRCUITS[0]), racers=racers)
    for index, racer in enumerate(racers):
        racer.finished = True
        racer.finish_time = 10 + index
    results = race.result_records(1)
    assert [result.points_awarded for result in results] == [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
    entries = [ChampionshipEntry(racer.id, racer.name) for racer in racers]
    award_results(entries, results)
    assert [entry.racer_id for entry in standings(entries)] == list(range(10))


def test_closed_road_and_low_fuel_do_not_permit_illegal_move():
    race = Race(load_circuit(CIRCUITS[0]))
    human = race.racers[0]
    target, road = race.options(human)[0]
    road.status = "blocked"
    assert not race.choose(0, target)
    road.status = "open"
    human.fuel = 0
    assert race.choose(0, target)
    race.tick(.1)
    assert human.dnf and human.edge_id is None
    assert not race.choose(0, target)


def test_out_of_order_checkpoint_and_early_start_crossing_do_not_count():
    race = Race(load_circuit(CIRCUITS[0]))
    human = race.racers[0]
    assert race.choose(0, 10)
    while human.vertex != 10:
        race.tick(.1)
    assert human.next_checkpoint == 0 and human.laps == 0
    assert race.choose(0, 0)
    while human.vertex != 0:
        race.tick(.1)
    assert human.next_checkpoint == 0 and human.laps == 0


def test_no_route_waits_until_a_closure_expires():
    race = Race(load_circuit(CIRCUITS[0]))
    for index, (_, edge) in enumerate(race.options(race.racers[1])):
        race.schedule(Event(100 + index, .1, 1, "block", edge.id, 1))
    race.tick(.1)
    assert race.racers[1].status == "waiting for a route"
    assert not race.racers[1].dnf
    for _ in range(15):
        race.tick(.1)
    assert race.racers[1].status == "racing"


@pytest.mark.parametrize("seed", range(5))
def test_generated_circuits_can_be_raced_without_opponent_shortcut_loops(seed):
    race = Race(generate_circuit(seed))
    for _ in range(2400):
        human = race.racers[0]
        if human.edge_id is None and not human.finished and not human.dnf:
            future = set(race.circuit.checkpoints[human.next_checkpoint + 1:])
            route = shortest_path(race.circuit.graph, human.vertex, race._destination(human),
                                  avoid_vertices=future)
            if len(route.vertices) > 1:
                race.choose(0, route.vertices[1])
        race.tick(.1)
        if race.over:
            break
    assert all(racer.finished for racer in race.racers)
