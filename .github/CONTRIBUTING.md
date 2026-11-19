# Working on REDLINE

Keep the project focused on the assignment while making the racing experience
clear and enjoyable to play.

## Pull request workflow

1. Pick an open issue or create one with a short description.
2. Add a few relevant labels and assign a teammate who will coordinate the work.
3. Create a short-lived branch from `main`, such as `feature/animated-dashboard`
   or `fix/checkpoint-order`.
4. Open a pull request to `main` when the change is ready for teammate feedback.
   The `checks` and `package-smoke` CI jobs must pass before merging; no approval
   is required.
5. Include relevant test results. For visible changes, add a screenshot or
   recording and check normal and reduced-motion behavior.
6. Merge the pull request and delete the temporary branch.

There is no permanent `game` branch or phase-gate process. Teammates can adjust
the issue scope and split or combine work as the project develops.
The [development workflow](../docs/development-workflow.md) maps the full
assignment and bonuses to the work and describes integration and submission.

## Project conventions

- Keep algorithm implementations independent from Pygame rendering.
- Let gameplay and the Algorithm Lab use the same algorithm implementation.
- Use fixed seeds and stable tie-breaking for repeatable opponents and events.
- Add tests as real functionality is implemented; do not add placeholder tests.
- Keep the code readable enough for every group member to explain in a viva.
- Keep animation tied to actual game state and outside the simulation clock.
- Record new asset provenance in the matching `assets/` README.

## Local checks

Install the development environment with:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then run:

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests experiments scripts
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pip check
```

The CI `checks` and `package-smoke` jobs must pass before a PR is merged.
The `checks` job also renders the interface and builds the draft report; the
packaging job builds and launches the Windows executable and exercises a
test-only archive. That archive is not the final coursework submission.

