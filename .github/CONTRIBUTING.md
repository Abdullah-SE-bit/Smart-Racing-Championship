# Working on Smart Racing Championship

Keep the project focused on the assignment while making the racing experience
clear and enjoyable to play.

## Simple workflow

1. Pick an open issue or create one with a short description.
2. Add a few relevant labels and assign a teammate who will coordinate the work.
3. Create a short-lived branch from `main`, such as `feature/animated-dashboard`
   or `fix/checkpoint-order`.
4. Open a pull request to `main` when the change is ready for teammate feedback.
   The Python CI check must pass before merging; no approval is required.
5. Include relevant test results. For UI work, add a screenshot or recording.
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

