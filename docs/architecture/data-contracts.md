# Data contracts and serialization

The models are plain Python and do not import Pygame. IDs are integers and are
looked up by value, not by list position. A graph owns each vertex and edge ID
once. It uses adjacency lists sorted by neighbor and edge ID for stable traversal.
Undirected roads are represented in both adjacency lists; a directed road is
traversable only from `source` to `target`. Blocked roads are omitted from
neighbor iteration; restricted roads remain traversable with updated costs.

`Vertex` stores ID, finite map coordinates, kind, optional positive checkpoint
order and service availability. `Edge` stores ID, endpoints, non-negative finite
distance, base time, fuel and obstacle cost, difficulty 1-5, status, direction
and shortcut flags. Costs and profile weights must be non-negative; reference
values are strictly positive. Circuit validation adds the assignment's ordered
checkpoint, topology, obstacle, service and fuel-plan requirements.

`data/circuits/*.json` and saved circuits use the same schema: a name, start
vertex, ordered checkpoint IDs, main-route vertex IDs, and arrays of vertex and
edge records matching the model field names. The loader checks endpoints,
duplicate IDs, fields and circuit constraints. `save_circuit` writes this same
schema as UTF-8 JSON and validates first; a round-trip test checks both records
and roads. Runtime race effects and progress are not persisted in circuit files.
Alternative-lap validation searches for two simple, ordered laps with a 50,000
state limit; reaching that limit without two results is reported as inconclusive.

`Racer` contains its stable ID, name, strategy, vertex and resource/progress
state. `Event` contains an ID, trigger time, priority, target, kind, duration and
cancellation flag. The event queue assigns the insertion sequence so equal-time
events remain deterministic. It rejects duplicate IDs even after extraction.

Once a race is over, `Race.result_records(race_id)` returns immutable
`RaceResult` records with race and racer IDs, position, optional finish and lap
times, bonus points, points awarded and finish status. No result record is
produced before the race ends. Championship entries contain racer ID, points,
wins, sum of positions and best lap; the ranking comparator is shared by all
sorting methods and top-k retrieval. Unfinished racers have no finish time and
earn no points under the current documented rule.
