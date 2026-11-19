# Circuit data

The JSON files in this directory define the three authored racing circuits.
Each file is loaded into the shared adjacency-list model by
`smart_racing.tracks.circuits.load_circuit` and checked by
`validate_circuit` before it is used.

## File shape

- `name`: display name for the venue.
- `start`: integer ID of the start/finish vertex.
- `checkpoints`: vertex IDs in mandatory visit order.
- `main_route`: recommended route vertex IDs, beginning and ending at `start`
  and passing through the checkpoints in order.
- `vertices`: records with `id`, `x`, `y`, `kind`, optional
  `checkpoint_order`, and service `active` state.
- `edges`: records with `id`, `source`, `target`, `distance`, `base_time`,
  `fuel_cost`, `difficulty`, `status`, `shortcut`, `directed`, and `obstacle`.

Vertex kinds are `start`, `finish`, `checkpoint`, `intersection`, `fuel`,
`nitro`, and `dead_end`. Road status is `open`, `blocked`, or `restricted`;
one-way roads set `directed` to `true`. Costs must be finite and non-negative,
and difficulty is an integer from 1 through 5.

## Editing safely

Keep IDs unique and endpoints valid. Preserve at least ten ordered checkpoints,
two shortcuts, a cycle, a dead end, several intersections, an obstacle, and
fuel/nitro services. The validator also checks ordered lap reachability,
alternative laps, and full-tank fuel feasibility. Do not infer validity from a
JSON parser alone.

After editing, run the full project tests from the repository root:

```powershell
python -m pytest
```

The authored circuit requirements have a dedicated regression check in
`tests/integration/test_race.py`.
