"""Kruskal minimum spanning tree on an undirected candidate graph."""

from smart_racing.core.graph import Graph
from smart_racing.algorithms.sorting.rankings import merge_sort


def kruskal(graph: Graph, trace: list[dict] | None = None) -> list[int]:
    if any(edge.directed for edge in graph.edges.values()):
        raise ValueError("MST candidates must be undirected")
    parent = {vertex: vertex for vertex in graph.vertices}
    rank = {vertex: 0 for vertex in graph.vertices}

    def root(vertex):
        while parent[vertex] != vertex:
            parent[vertex] = parent[parent[vertex]]
            vertex = parent[vertex]
        return vertex

    result = []
    for edge in merge_sort(graph.edges.values(), key=lambda edge: (edge.distance, edge.id)):
        if edge.status == "blocked":
            continue
        a, b = root(edge.source), root(edge.target)
        if a == b:
            continue
        if rank[a] < rank[b]:
            a, b = b, a
        parent[b] = a
        if rank[a] == rank[b]:
            rank[a] += 1
        result.append(edge.id)
        if trace is not None:
            trace.append({"action": "accept mst road", "edge": edge.id, "value": round(edge.distance, 2)})
    if graph.vertices and len(result) != len(graph.vertices) - 1:
        raise ValueError("Candidate graph is disconnected")
    return result
