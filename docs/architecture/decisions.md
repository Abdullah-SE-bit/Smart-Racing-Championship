# Architecture and rules in the current prototype

Implementation is in progress. This document describes the code that exists,
including its current limitations; it is not a claim of assignment completion.

## Boundaries

Saved-circuit vertex and road IDs are identifiers, not array positions. The
planner initializes its endpoints from the selected circuit, while the default
race events select from sorted existing road IDs. This keeps events deterministic
for authored, generated, and saved tracks with nonconsecutive IDs. Validation
reports unknown main-route vertices before accessing adjacency lists.

Seeded generation can optionally emit plain-data stage records. The circuit
workshop reveals those records, including validation rejection and retry reasons,
without adding presentation dependencies to the generator. The invalid-track
demonstration validates a copy with its shortcut flags removed.

The generator builds an undirected complete candidate graph over its non-dead-end
vertices. Kruskal rejects directed candidates and raises a disconnected-graph
error if open edges cannot join every vertex; it does not silently accept a
forest as a circuit backbone. Backtracking rejects incompatible checkpoint
orders, services less than 120 coordinate units apart, and obstacle roads that
share endpoints or are bridges. These checks only reject placements that violate
the chosen constraints. Candidate generation or validation failures retry with
the same seed and a deterministic attempt index, up to five attempts by default.
Backtracking can still take exponential time in its candidate count; the fixed
candidate sets and retry limit bound work in the current generator.

- `core/graph.py` contains Pygame-independent vertices, edges, adjacency lists
  and non-negative cost profiles. Algorithms receive these objects and return
  plain results and traces. They do not import the presentation layer.
- `game/race.py` owns racers, checkpoint progression, resources, event effects
  and results. `game/clock.py` converts frame times into fixed 1/30-second
  simulation steps; the UI caps a single frame's accumulated time at 0.1 second
  after a stall. Rendering observes state and does not choose outcomes.
- `tracks/` loads and checks JSON circuits. The seeded generator builds an
  undirected Kruskal backbone and adds a lap and alternatives. Backtracking
  places ordered checkpoints on adjacent ring positions, chooses fuel and
  nitro service locations at least 120 map units apart, and selects two
  edge-disjoint obstacle roads that are not bridges or part of the main loop.
  The ring constraint prunes placements that cannot form this generated loop;
  bridge and spacing checks protect connectivity and separate the obstacles.
  After building this undirected structure, generation adds two seeded one-way
  roads from loop vertices to service-area vertices without duplicating an
  existing road. The ordinary directed-graph validator checks the final
  circuit, including checkpoint order, lap return, alternatives and fuel.
  Candidate generation retries at most five deterministic seed variants by
  default and reports failure rather than exposing an invalid circuit.
- The planner, lab and experiments invoke the same algorithm functions. The
  lab uses their traces; sorting in the standings and heap top-k share
  `championship.standings.ranking_key`.

## Current tuned values and rules

- Two laps by default, selectable as two or three. Default race limit is 240
  seconds, selectable as 180, 240 or 360. A time-limited unfinished racer is
  ranked by laps, checkpoints, elapsed time and ID and earns no points.
- Fuel capacity is 100; the cost of an edge is its `fuel_cost` multiplied by
  `1 + 0.1 * (difficulty - 1)`. A station supplies up to 40 units once per
  visit and takes three seconds. Human players press F; opponents stop below
  25 units at active stations.
- Below 25 units, the main-route and shortcut opponents consider reachable
  active fuel stations in ascending vertex ID order, excluding routes through
  later checkpoints. The distance opponent checks for a reachable active
  station along its current shortest route to the next checkpoint. All three
  refuel on arrival and then resume their respective routing policies.
- The shortcut opponent considers open shortcut roads reachable before the
  next required checkpoint. For each orientation it finds a distance-based
  approach and an exit to that checkpoint, avoiding later checkpoints and
  vertices already visited on the current leg. It conservatively requires
  enough current fuel for that candidate without another refuelling stop.
  Candidates are ordered by approach distance, road ID and endpoint IDs.
  The racer commits through the chosen shortcut; if a planned road closes, it
  discards that detour and chooses again or falls back to the main route.
- Roads are selected by edge ID as well as destination. When multiple open
  roads share endpoints, the human interface sends the selected ID and the AI
  preserves IDs from its searches and planned detours. A destination-only
  human command is accepted only when exactly one open road reaches it. If the
  selected road closes before entry, the racer does not silently take a
  different parallel road.
- The initial nitro allocation is one charge, capacity three. A charge lasts
  four simulation seconds, multiplies speed by 1.5 and doubles fuel for the
  boosted portion. Pickup vertices are consumed after collection. Resource
  actions and finish events are reported by the engine for the race HUD.
- A blocked road cannot be entered. A restriction multiplies traversal time
  by 1.5; an oil effect also increases difficulty by one, capped at five.
  Events at a tick are processed in `(time, priority, sequence)` order before
  racer decisions; each temporary effect schedules its own deterministic heap
  expiration, and active effects are recomputed together. Negative event IDs
  are reserved for internal expiration records.
  A permanent or temporary closure takes precedence over oil and speed
  restrictions. A temporary shortcut-open effect can open a baseline-blocked
  shortcut, but another active closure still wins; any active restrictions
  apply while the shortcut is open. Persistent road blocks and persistent
  shortcut open/close states are stored independently: unblocking a road does
  not erase a separately closed shortcut, and opening a shortcut does not erase
  a road block. Each expiry recomputes from the remaining effects and baseline
  status.
  A racer already on a road finishes crossing it before choosing a new road.
  If a chosen road closes before entry, the engine records an unavailable-road
  status. Insufficient fuel also produces status feedback. The race screen
  warns when the ordered route cannot currently be found.
- When no route exists, opponents wait and retry after the road state changes.
  A racer with no affordable outgoing edge and no available refuelling option
  is DNF; the time limit resolves other prolonged waits. Unaffordable selected
  roads are rejected if another affordable road exists.
- Fixed detours calculate checkpoint progress from the actual main route, which
  may include intermediate services or intersections. Refuelling searches avoid
  later checkpoints; neither kind of detour is allowed to visit them early.
- The score table is 25, 18, 15, 12, 10, 8, 6, 4, 2, 1. There are no bonus
  points. Championship ties use wins, sum of positions, best lap, then racer ID.

## Route costs

The scalar is a sum of non-negative weighted terms. Distance is divided by 100,
time by 10, difficulty-adjusted fuel by 10, difficulty penalty by 4, and
obstacle penalty by 1. Balanced weights are all one. Speed uses weights
`(.2, 3, .2, .2, .3)`, economy `(.3, .2, 3, .3, .2)`, and safety
`(.3, .3, .3, 3, 3)` in that order. A restriction multiplies the time term by
1.5. Scalar scores from different presets are not directly comparable.

A* multiplies Euclidean distance by the minimum current edge cost per geometric
distance. This is a consistent lower bound; if the minimum is zero, A* falls
back to zero heuristic. Checkpoint route legs exclude later mandatory
checkpoints. A single-pickup recommendation checks the estimated detour and
fuel requirement independently rather than mixing fuel and distance budgets.

## Known work still needed

The current screens and simulation are a prototype, not final evidence of full
assignment coverage. In particular, generated circuits are limited to a ring
layout with extra roads; additional generation constraints and route recovery
cases need review. Manual play testing and a
final submission check remain. The Windows executable built locally but was
blocked by the host's Application Control policy when a launch was attempted.
Do not report that launch as passed.
