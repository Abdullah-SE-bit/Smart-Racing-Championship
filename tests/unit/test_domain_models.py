from math import inf, nan
from pathlib import Path

import pytest

from smart_racing.championship.standings import ChampionshipEntry, award_results
from smart_racing.core.graph import CostProfile, Edge, Graph, Vertex
from smart_racing.core.records import RaceResult
from smart_racing.events.queue import Event, EventQueue
from smart_racing.game.race import Race, Racer
from smart_racing.tracks.circuits import load_circuit, save_circuit


@pytest.mark.parametrize("create", [
    lambda: Vertex(True, 0, 0),
    lambda: Vertex(1, nan, 0),
    lambda: Vertex(1, "bad", 0),
    lambda: Vertex(1, 0, 0, kind="unknown"),
    lambda: Vertex(1, 0, 0, checkpoint_order=1),
    lambda: Edge(1, 0, 1, -1, 1, 1),
    lambda: Edge(1, 0, 1, 1, inf, 1),
    lambda: Edge(1, 0, 1, 1, 1, 1, difficulty=2.0),
    lambda: Edge(1, 0, 1, 1, 1, 1, status="unknown"),
    lambda: CostProfile(distance=-1),
    lambda: CostProfile(distance_reference=0),
    lambda: Racer(1, "", "human", 0),
    lambda: Racer(1, "A", "human", 0, fuel=101),
    lambda: Event(1, nan, 1, "block", 0),
    lambda: Event(1, 0, 1, "block", 0, insertion_sequence=4),
    lambda: ChampionshipEntry(1, "A", total_points=-1),
    lambda: RaceResult(1, 2, 1, None, None, 0, 25, True),
    lambda: RaceResult(1, 2, 1, 5, nan, 0, 25, True),
])
def test_invalid_records_are_rejected(create):
    with pytest.raises(ValueError):
        create()


def test_graph_preserves_ids_direction_and_blocked_status():
    graph = Graph()
    graph.add_vertex(Vertex(10, 0, 0))
    graph.add_vertex(Vertex(20, 1, 0))
    graph.add_edge(Edge(99, 10, 20, 1, 1, 1, directed=True))
    assert [(neighbor, edge.id) for neighbor, edge in graph.neighbors(10)] == [(20, 99)]
    assert list(graph.neighbors(20)) == []
    with pytest.raises(ValueError, match="Duplicate"):
        graph.add_edge(Edge(99, 20, 10, 1, 1, 1))
    with pytest.raises(ValueError, match="endpoints"):
        graph.add_edge(Edge(100, 10, 30, 1, 1, 1))
    graph.edges[99].status = "blocked"
    assert list(graph.neighbors(10)) == []


def test_event_sequence_is_assigned_and_result_records_are_stable(tmp_path):
    circuit = load_circuit(Path("data/circuits/circuit_1.json"))
    saved = tmp_path / "circuit.json"
    save_circuit(circuit, saved)
    restored = load_circuit(saved)
    assert restored.graph.vertices == circuit.graph.vertices
    assert restored.graph.edges == circuit.graph.edges
    queue = EventQueue()
    first, second = Event(30, 1, 1, "block", 0), Event(20, 1, 1, "block", 0)
    queue.schedule(first)
    queue.schedule(second)
    assert [first.insertion_sequence, second.insertion_sequence] == [0, 1]
    assert [event.id for event in queue.due(1)] == [30, 20]
    race = Race(restored, time_limit=1, racers=[Racer(42, "Driver", "human", 0)])
    assert race.choose(42, 1)
    with pytest.raises(ValueError, match="Unknown racer"):
        race.choose(0, 1)
    with pytest.raises(ValueError, match="when the race ends"):
        race.result_records(7)
    with pytest.raises(ValueError, match="finite"):
        race.tick(nan)
    race.tick(1)
    record = race.result_records(7)[0]
    assert (record.race_id, record.racer_id, record.finish_position, record.finish_time) == (7, 42, 1, None)
    entries = [ChampionshipEntry(42, "Driver")]
    award_results(entries, [record])
    assert entries[0].total_points == 0
