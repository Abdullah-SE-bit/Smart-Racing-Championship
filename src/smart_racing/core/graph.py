"""Presentation-independent circuit graph and road cost model."""

from dataclasses import dataclass, field
from math import isfinite
from numbers import Real


@dataclass(frozen=True, slots=True)
class Vertex:
    id: int
    x: float
    y: float
    kind: str = "intersection"
    checkpoint_order: int | None = None
    active: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.id, bool) or not isinstance(self.id, int):
            raise ValueError("Vertex ID must be an integer")
        if any(isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) for value in (self.x, self.y)):
            raise ValueError("Vertex coordinates must be finite")
        if self.kind not in {"start", "finish", "checkpoint", "intersection", "fuel", "nitro", "dead_end"}:
            raise ValueError("Invalid vertex kind")
        if self.checkpoint_order is not None and (isinstance(self.checkpoint_order, bool)
                                                   or not isinstance(self.checkpoint_order, int)
                                                   or self.checkpoint_order < 1):
            raise ValueError("Checkpoint order must be a positive integer")
        if self.kind != "checkpoint" and self.checkpoint_order is not None:
            raise ValueError("Only checkpoints can have checkpoint order")
        if not isinstance(self.active, bool):
            raise ValueError("Service availability must be boolean")


@dataclass(slots=True)
class Edge:
    id: int
    source: int
    target: int
    distance: float
    base_time: float
    fuel_cost: float
    difficulty: int = 1
    status: str = "open"
    shortcut: bool = False
    directed: bool = False
    obstacle: float = 0.0

    def __post_init__(self) -> None:
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (self.id, self.source, self.target)):
            raise ValueError("Road ID and endpoints must be integers")
        values = (self.distance, self.base_time, self.fuel_cost, self.obstacle)
        if any(isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or value < 0 for value in values):
            raise ValueError("Road costs must be finite and non-negative")
        if isinstance(self.difficulty, bool) or not isinstance(self.difficulty, int) or self.difficulty not in range(1, 6):
            raise ValueError("Road difficulty must be between 1 and 5")
        if self.status not in {"open", "blocked", "restricted"}:
            raise ValueError("Invalid road status")
        if not isinstance(self.shortcut, bool) or not isinstance(self.directed, bool):
            raise ValueError("Shortcut and direction flags must be boolean")


@dataclass(frozen=True, slots=True)
class CostProfile:
    """Weights and reference values for one non-negative scalar route cost."""

    distance: float = 1.0
    time: float = 1.0
    fuel: float = 1.0
    difficulty: float = 1.0
    obstacle: float = 1.0
    distance_reference: float = 100.0
    time_reference: float = 10.0
    fuel_reference: float = 10.0
    obstacle_reference: float = 1.0

    def __post_init__(self) -> None:
        weights = (self.distance, self.time, self.fuel, self.difficulty, self.obstacle)
        references = (self.distance_reference, self.time_reference,
                      self.fuel_reference, self.obstacle_reference)
        if any(isinstance(n, bool) or not isinstance(n, Real) or not isfinite(n) or n < 0 for n in weights):
            raise ValueError("Weights must be finite and non-negative")
        if any(isinstance(n, bool) or not isinstance(n, Real) or not isfinite(n) or n <= 0 for n in references):
            raise ValueError("Reference values must be finite and positive")

    def cost(self, edge: Edge) -> float:
        restriction = 1.5 if edge.status == "restricted" else 1.0
        return (self.distance * edge.distance / self.distance_reference
                + self.time * edge.base_time * restriction / self.time_reference
                + self.fuel * edge.fuel_cost * (1 + 0.1 * (edge.difficulty - 1)) / self.fuel_reference
                + self.difficulty * (edge.difficulty - 1) / 4
                + self.obstacle * edge.obstacle / self.obstacle_reference)


@dataclass(slots=True)
class Graph:
    vertices: dict[int, Vertex] = field(default_factory=dict)
    edges: dict[int, Edge] = field(default_factory=dict)
    adjacency: dict[int, list[tuple[int, int]]] = field(default_factory=dict)

    def add_vertex(self, vertex: Vertex) -> None:
        if vertex.id in self.vertices:
            raise ValueError(f"Duplicate vertex {vertex.id}")
        self.vertices[vertex.id] = vertex
        self.adjacency[vertex.id] = []

    def add_edge(self, edge: Edge) -> None:
        if edge.id in self.edges:
            raise ValueError(f"Duplicate edge {edge.id}")
        if edge.source not in self.vertices or edge.target not in self.vertices:
            raise ValueError("Both road endpoints must exist")
        self.edges[edge.id] = edge
        self.adjacency[edge.source].append((edge.target, edge.id))
        if not edge.directed and edge.source != edge.target:
            self.adjacency[edge.target].append((edge.source, edge.id))
        self.adjacency[edge.source].sort()
        self.adjacency[edge.target].sort()

    def neighbors(self, vertex: int):
        for target, edge_id in self.adjacency[vertex]:
            edge = self.edges[edge_id]
            if edge.status != "blocked":
                yield target, edge
