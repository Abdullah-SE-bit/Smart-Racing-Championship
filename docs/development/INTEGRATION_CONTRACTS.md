# Proposed integration contracts

Documentation only: no Python interfaces are implemented. **All field choices,
units, and unresolved semantics require team approval** and PDF verification.
Use plain Python/JSON-compatible data at boundaries; never Pygame objects in
algorithm or domain contracts. Consumers must not introduce circular imports.

| Contract | Proposed information | Invariants and open decisions |
| --- | --- | --- |
| Graph / edge | Stable node and edge identifiers, endpoints, position for rendering, cost, access/closure state, graph revision | Decide directedness, parallel edges, cost units, representation and mutability. Dijkstra/A* need nonnegative weights; define unreachable and invalid-input handling. |
| Route request | Graph revision, source, destination or ordered remaining checkpoints, active constraints, strategy | Decide checkpoint planning granularity and resource-state expansion. Stable neighbor/tie order must be explicit. |
| Route result | Success/unreachable/invalid status, node or edge sequence, cost, graph revision, metrics | Verify each edge exists and respects constraints; stale graph revisions trigger explicit handling. Empty path versus failure must be distinct. |
| Racer state | Racer ID, current edge/location, next checkpoint index, completion/DNF status, resources, simulation tick | Decide movement units, checkpoint crossing semantics, laps, collision policy, DNF conditions and tie rules. UI reads state, engine changes it. |
| Race event | Event ID/type, scheduled tick, expiry tick, stable insertion sequence, affected roads, payload | Decide same-tick ordering, closure precedence and expiry semantics. Engine-controlled clock; event ties must not use wall time. |
| Fuel / nitro | Current quantity, capacity, consumption, pickup/refuel effects | Decide units, discretization, boost behavior and rounding. Quantities remain within agreed bounds; feasibility must match route constraints. |
| Championship result | Race/circuit/racer IDs, finish or DNF, elapsed simulation time, points, rank and tie keys | Points, DNF ordering and championship tie rules await assignment verification. Preserve raw results independently of displayed order. |
| Algorithm metrics | Algorithm/version, input ID/size, seed, operation counts, result, optional elapsed time and trace | Decide counters and trace schema. Rendering consumes traces from the same gameplay implementation. Runtime measurements must not change algorithm decisions. |

Agree serialization/versioning and validation ownership before storing circuit
or result schemas. Record accepted changes and migration implications in
[DECISIONS.md](DECISIONS.md), update producers/consumers in dependency order,
and add contract tests. Do not mistake this proposal for approved game rules.
