# Demo and viva preparation

This guide is a rehearsal aid for the current implementation. Each group member
should run the application, inspect the source and explain the work in their own
words. The commands and results below do not constitute a coursework submission.

## Before the demonstration

1. On a Windows machine that permits the application to run, follow the setup
   instructions in `README.md`. Launch with `python -m smart_racing`, or use the
   built executable after verifying it on that machine.
2. Run the automated suite and `pip check`. GitHub Actions also tests a packaged
   Windows executable in headless mode and publishes screen previews. Those
   checks do not replace a human playthrough.
3. Rehearse one complete quick race and the three-race championship, including
   resource use, a road event, results and standings. Record any actual failures.
4. Open `docs/assignment-specification.md`, `docs/architecture/decisions.md`,
   `docs/algorithms/implementation-map.md` and `experiments/results/analysis.md`
   so the group can connect the demonstration to requirements and evidence.

## Suggested walkthrough

1. **Menu and setup:** choose a circuit, show the controls and change a setting.
   Explain that the window scales and that reduced motion is available.
2. **Planner:** select start and destination vertices, compare the four cost
   presets, show the ordered-lap option and inspect bounded alternatives. Explain
   that endpoint alternatives do not enforce checkpoint order, while ordered
   routes do. A preset score is meaningful for its own weights; scores from
   different presets are not directly comparable.
3. **Generated circuit:** generate a track, show its seed and generation stages,
   and use the invalid-track button to show a real validation error. Return to
   the planner and save the valid circuit if desired.
4. **Algorithm Lab:** select BFS, Dijkstra, DP, the event heap and a sorting
   method. Use step, play, pause, reset and speed controls. Point to the shared
   code in `src/smart_racing/algorithms/`; the Lab consumes those functions and
   their plain-data traces.
5. **Race:** start a quick race or championship. Select roads with the arrow
   keys and Enter, use N for nitro, and F at an available fuel station. Show
   checkpoint order, the moving cars, fuel, nitro, route highlighting and event
   feedback. Space pauses; Escape returns to the menu. Race outcomes depend on
   the player's actual actions and should not be presented as predetermined.
6. **Results:** finish the race or wait for the time limit. Show results,
   standings, the sort selector and the selectable top-k view. In championship
   mode, continue through the planner to the next circuit.
7. **Evidence:** open the five experiment tables and raw measurements. Explain
   the input sizes, repeated runs and limitations before comparing timings.

## Viva prompts

- **Graph and timing:** Why use adjacency lists? How are directed, blocked and
  restricted roads represented? Why does a fixed simulation step prevent frame
  rate from changing the race outcome?
- **BFS and DFS:** BFS minimizes edge count, not distance. Explain the FIFO queue,
  parent reconstruction, DFS visited set, cycle analysis and why enumerating
  simple alternatives needs limits.
- **Dijkstra and A-star:** Explain non-negative normalized costs, relaxation,
  heap entries and blocked-road replanning. The A-star heuristic uses a proven
  minimum cost per geometric unit and may be zero; it does not always expand
  fewer vertices. Explain why checkpoint legs exclude later checkpoints.
- **Resources:** Explain the 0/1 knapsack recurrence and reconstruction, the
  conservative tenths-of-fuel refuelling model, and the distinction between
  fuel, time and nitro. In the assignment example, greedy obtains benefit 30
  while DP obtains 48; the tracked study contains two more counterexamples.
- **Generation:** Explain Kruskal's union-find cycle check, rejection of a
  disconnected candidate, backtracking constraints, the recorded seed and the
  bounded retry policy. Generated layouts are restricted to a ring-based family.
- **Events and rankings:** Explain heap ordering by time, priority and insertion
  sequence, lazy cancellation, independent expiry, the points table and all
  championship tie-breaks. Compare Merge, Quick and Heap Sort with heap top-k.
- **Experiments:** Identify the machine, dependency versions, seed, warm-up,
  repetitions, timed regions and raw samples. Timings are measurements from one
  environment and do not by themselves prove asymptotic complexity.

## Still needed before a later submission

Complete a human playthrough and executable check on an allowed machine, add
the actual group names, registration numbers and section, finalize the report,
and inspect a correctly named archive after extraction. Ensure each group
member is ready for the demonstration and viva. Do not upload anything until
the group chooses to submit.
