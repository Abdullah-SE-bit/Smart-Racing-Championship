# Initial architectural dependencies

This is an initial dependency graph, **not an approved implementation schedule**.
No dates or completed feature work are implied. Validate against `Project.pdf`
when supplied; some dependencies may be refined during contract review.

```text
Graph data model
  +-- BFS / DFS
  +-- Dijkstra / A* --> Route planner --> Racing engine
  |                                      +-- Events
  |                                      +-- Opponents
  |                                      +-- Resources
  +-- Track validation --> MST / Backtracking

Racing engine
  +-- Pygame racing UI
  +-- Algorithm Lab integration (also depends on shared algorithms)
  +-- Championship results --> Sorting / Top-k integration

All implemented modules
  +-- Integration testing
  +-- Experimental studies
  +-- Final Windows packaging
```

Sorting algorithm unit work can proceed independently of championship consumers.
Resource optimization likewise depends on agreed constraints before engine
integration. The graph shows integration relationships, not a requirement to
delay independent algorithm tests until an entire subsystem exists.

Resolve graph representation, weight semantics, route failure states, simulation
clock, and stable tie rules early. Interface decisions need team approval;
implementation still needs explicit user instruction and a scoped issue.
