"""Checks for the independent correctness reference used in the studies."""

from pathlib import Path
import runpy

from smart_racing.core.graph import Edge, Graph, Vertex


def test_minimum_hops_reference_handles_direction_and_unreachable_vertices():
    namespace = runpy.run_path(str(Path("experiments/benchmarks/run_studies.py")))
    reference = namespace["reference_minimum_hops"]
    graph = Graph()
    for vertex in range(5):
        graph.add_vertex(Vertex(vertex, vertex, 0))
    graph.add_edge(Edge(0, 0, 1, 1, 1, 1, directed=True))
    graph.add_edge(Edge(1, 1, 2, 1, 1, 1, directed=True))
    graph.add_edge(Edge(2, 0, 2, 10, 10, 10, directed=True))
    graph.add_edge(Edge(3, 2, 3, 1, 1, 1, status="blocked"))
    assert reference(graph, 0) == {0: 0, 1: 1, 2: 1}
    assert reference(graph, 2) == {2: 0}
