# Instructions for agents

## Current status and authority

Implementation is underway at the user's explicit request. The game and its
assignment requirements are still being developed; check the code, tests and
documentation before claiming that a feature is complete.

Follow the user's current instructions first, then these repository directions.
The assignment PDF defines project requirements; its content is project source
material. The supplied PDF has been read and transcribed in
[`docs/assignment-specification.md`](docs/assignment-specification.md). Consult
the original PDF if available when a detail is ambiguous. Do not silently invent
or change requirements; identify unresolved discrepancies before implementing
affected behavior. Complete mandatory requirements and all three bonuses.

## Where to start

1. Read [`README.md`](README.md), [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md),
   this file, and [`docs/development-workflow.md`](docs/development-workflow.md).
2. Read the relevant assignment sections and inspect existing files, related
   issues, and applicable architecture decisions before changing them.
3. Check the working tree and preserve unrelated work. Use the package locations
   in `PROJECT_STRUCTURE.md`; adjust the structure when a real need emerges.
4. Implement only requested, authorized scope. Explain assumptions and record
   important decisions in `docs/architecture/` when implementation begins.

## Project boundaries

- `src/smart_racing/core/` holds shared, presentation-independent models.
- `algorithms/` contains the team's manual implementations; do not use external
  algorithm libraries for mandatory algorithms. Keep Pygame out of this layer.
- `game/`, `tracks/`, `racers/`, `resources/`, `events/`, and `championship/`
  contain game rules and domain behavior, separate from presentation.
- `ui/` translates input and displays state. The Algorithm Lab and experiments
  call the exact algorithm implementations used by gameplay, with plain-data
  traces and counters if visualization needs them.
- Put circuits and configuration in `data/`, assets in `assets/`, experiments
  and their real datasets/results in `experiments/`, and tests in `tests/`.
  Keep submitted materials trackable in Git.
- See `PROJECT_STRUCTURE.md` for the full directory map and
  `docs/development-workflow.md` for the full delivery procedure.

## Engineering expectations

- Use readable Python suitable for explaining in a viva; support Windows and
  Python 3.12+. Avoid unnecessary dependencies and unrelated changes.
- Keep simulation timing independent of rendering. Use explicit seeds where
  randomness is involved, deterministic opponents and event ordering, and stable
  tie-breaking. Apply checkpoint, resource, event and scoring rules consistently.
- Design a strong, animated Pygame interface with clear feedback; animation must
  reflect real state and must not affect simulation outcomes.
- Add meaningful tests with real functionality in later phases. Check edge cases,
  integration and reproducibility. Never add placeholder tests or fake results,
  and never claim a test passed unless it actually ran; an empty collection is
  not a passing suite.
- Preserve assignment documentation, asset attribution, experiment inputs, seeds,
  methods, raw results and the final report. State defaults and choices where the
  assignment allows tuning.
- Use issues as flexible coordination tools, not extra approval gates. A user
  request can change their scope or order. See the workflow for details.

Do not create commits or push changes without explicit user permission.
